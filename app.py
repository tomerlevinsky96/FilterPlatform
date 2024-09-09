import math
import os
from collections import defaultdict
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask import Response
import pandas as pd
import io
from flask import Flask, render_template, request, jsonify, send_file
import psycopg2
from psycopg2 import Error
import json
from openpyxl import Workbook
from io import BytesIO
import datetime
import re
from openpyxl.styles import Font, PatternFill

app = Flask(__name__, template_folder=os.path.abspath('Templates'))
app.secret_key = 'your_secret_key'  # Required for flash messaging


# Database connection settings
DB_CONFIG = {
    "user": 'postgres',
    "database":'appdata'
}

# Mapping between application and database column names
COLUMN_MAPPING = {
    "T1w": "t1w",
    "T2w": "t2w",
    "Flair": "flair",
    "Rest_fMRI": "restfmri",
    "Task_fMRI": "taskfmri",
    "dMRI_AP": "dmriap",
    "dMRI_PA": "dmripa",
    "MRTRIX": "mrtrix",
    "AxSI": "axsi",
    "QSI": "qsi",
    "HCP_freesurfer": "hcpfreesurfer",
    "HCP_Rest_fMRI": "hcprestfmri",
    "HCP_Task_fMRI": "hcptaskfmri",
    "HCP_diffusion": "hcpdiffusion"
}

# List of all available scan types
SCAN_TYPES = list(COLUMN_MAPPING.keys())

# Columns to exclude
EXCLUDE_COLUMNS = ['path', 'datetimescan']


def connect_to_db():
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        connection.autocommit = True
        return connection
    except Error as e:
        print(f"Error while connecting to PostgreSQL: {e}")
        return None

###########################################filter2 functions
def flatten_values(value):
    if isinstance(value, tuple):
        return list(value)  # Convert tuple to list to extend it
    else:
        return [value]  # Return value as a list


def get_all_columns(connection, table_name):
    try:
        cursor = connection.cursor()
        query = f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'"
        cursor.execute(query)
        columns = [row[0] for row in cursor.fetchall() if row[0] not in EXCLUDE_COLUMNS]
        cursor.close()
        return columns
    except Error as e:
        print(f"Error fetching columns from {table_name}:", e)
        return []

def get_distinct_values(connection, app_column_name):
    try:
        cursor = connection.cursor()
        sql_column_name = COLUMN_MAPPING.get(app_column_name)
        if sql_column_name is None:
            print(f"No mapping found for column: {app_column_name}")
            return []

        query = f"SELECT DISTINCT {sql_column_name} FROM scans"
        cursor.execute(query)

        values = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return values
    except Error as e:
        print(f"Error fetching distinct values for {app_column_name}:", e)
        return []

def build_and_execute_query(connection, selected_types, selected_genders, age_from, age_to, start_date_of_scan, start_hour_of_scan, end_date_of_scan, end_hour_of_scan, weight_from, weight_to,height_from,height_to,selected_patient_codes,Study,Group,Protocol,scan_number,Dominant_hand,update_subjects,Data_output):
    where_conditions = []
    params = []

    # Process selected types
    for scan_type, value in selected_types.items():
        db_column = COLUMN_MAPPING.get(scan_type)
        if db_column:
            if str(value) != 'None':
                if value.lower() == 'ok':
                    # Search for distinct values of the column
                    distinct_values = get_distinct_values(connection, scan_type)
                    # If 'OK' is one of the distinct values, add it to the search condition
                    if value.lower() in distinct_values:
                        where_conditions.append(f"{db_column} = 'ok'")
                    elif 'True' in distinct_values:
                        where_conditions.append(f"{db_column} = 'True'")

    # Process selected genders
    if selected_genders:
        gender_condition = f"gender IN ('{selected_genders}')"
        where_conditions.append(gender_condition)


    # Process age range
    if age_from:
        where_conditions.append(f"Ageofscan ~ '^[0-9]*\.?[0-9]+$' and  CAST(Ageofscan AS NUMERIC)>= '{age_from}'")
    if age_to:
        where_conditions.append(f"Ageofscan ~ '^[0-9]*\.?[0-9]+$' and  CAST(Ageofscan AS NUMERIC)<= '{age_to}'")
    if weight_from:
        where_conditions.append(f"weight ~ '^[0-9]*\.?[0-9]+$' and CAST(weight AS NUMERIC)>='{weight_from}'")
    if weight_to:
        where_conditions.append(f"weight ~ '^[0-9]*\.?[0-9]+$' and CAST(weight AS NUMERIC)<='{weight_to}'")
    if height_from:
        where_conditions.append(f"height ~ '^[0-9]*\.?[0-9]+$' and CAST(height AS NUMERIC)>= '{height_from}'")
    if height_to:
        where_conditions.append(f"height ~ '^[0-9]*\.?[0-9]+$' and CAST(height AS NUMERIC)<= '{height_to}'")
    if Study:
        where_conditions.append(f"study = '{Study}'")
    if Group:
        where_conditions.append(f"groupname = '{Group}'")
    if Protocol:
        where_conditions.append(f"protocol = '{Protocol}'")
    if scan_number:
        where_conditions.append(f"noscan = '{scan_number}'")


    if start_date_of_scan and end_date_of_scan and start_hour_of_scan and end_hour_of_scan:
        # If all date and time filters are present
        where_conditions.append(
            f"crf.datetimescan::date BETWEEN '{start_date_of_scan}' AND '{end_date_of_scan}' AND "
            f"crf.datetimescan::time BETWEEN '{start_hour_of_scan}' AND '{end_hour_of_scan}'"
        )

    elif start_date_of_scan and end_date_of_scan:
        # If only date filters are present
        where_conditions.append(
            f"crf.datetimescan::date BETWEEN '{start_date_of_scan}' AND '{end_date_of_scan}'"
        )

    elif start_date_of_scan and not end_date_of_scan and start_hour_of_scan and end_hour_of_scan:
        # If start date and time filters are present
        where_conditions.append(
            f"crf.datetimescan::date >= '{start_date_of_scan}' AND "
            f"crf.datetimescan::time BETWEEN '{start_hour_of_scan}' AND '{end_hour_of_scan}'"
        )

    elif end_date_of_scan and not start_date_of_scan and start_hour_of_scan and end_hour_of_scan:
        # If end date and time filters are present
        where_conditions.append(
            f"crf.datetimescan::date <= '{end_date_of_scan}' AND "
            f"crf.datetimescan::time BETWEEN '{start_hour_of_scan}' AND '{end_hour_of_scan}'"
        )

    elif start_hour_of_scan and end_hour_of_scan:
        # If only time filters are present
        where_conditions.append(
            f"crf.datetimescan::time BETWEEN '{start_hour_of_scan}' AND '{end_hour_of_scan}'"
        )

    elif start_date_of_scan:
        # If only start date is present
        where_conditions.append(f"crf.datetimescan::date >= '{start_date_of_scan}'")

    elif end_date_of_scan:
        # If only end date is present
        where_conditions.append(f"crf.datetimescan::date <= '{end_date_of_scan}'")

    # Process selected patient codes
    if update_subjects == 'no':
      if selected_patient_codes:
          patient_condition = f"subjects.questionairecode IN ({', '.join(map(repr, selected_patient_codes))})"
          where_conditions.append(patient_condition)

      if not where_conditions:
         return None


    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
    # Include the "path" column in the output
    if update_subjects=='yes':
       columns = f"""distinct(subjects.questionairecode)"""
    if update_subjects=='no':
        columns = ', '.join(column.strip("'") for column in Data_output)

    if Dominant_hand:
          query = f"""
                    SELECT {columns}
                    FROM subjects inner join crf on subjects.questionairecode=crf.questionairecode inner join answers on subjects.questionairecode=answers.questionairecode
                    INNER JOIN scans ON crf.datetimescan = scans.datetimescan
                    {where_clause};
                   """
    else:
          query = f"""
                    SELECT {columns}
                    FROM subjects inner join crf on subjects.questionairecode=crf.questionairecode
                    INNER JOIN scans ON crf.datetimescan = scans.datetimescan
                    {where_clause};
                    """

    try:
        cursor = connection.cursor()
        full_query = cursor.mogrify(query, params).decode('utf-8')
        print("Full query:", full_query)
        cursor.execute(full_query)
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error executing query: {e}")
        return None
##############################filters1 functions
def clean_value(value):
    if value == 'NaT' or value == 'nan' or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, datetime.datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return value

def append_and_color_header(worksheet, headers, background_color):
    worksheet.append(headers)
    for cell in worksheet[worksheet.max_row]:
        cell.fill = PatternFill(start_color=background_color, end_color=background_color, fill_type="solid")
        cell.font = Font(color="000000")  # Black text
def process_flexible_data(headers, patient_code, data):
    # Create a defaultdict to store all values for each column
    data = sorted(data, key=lambda x: x[0])

    # Group the data by the first element (column index)
    grouped_data = defaultdict(list)
    for key, value in data:
        grouped_data[key].append(value)

    # Determine the maximum number of repetitions for any key
    max_repetitions = max(len(values) for values in grouped_data.values())

    # Create the output rows
    output_rows = [[patient_code] for _ in range(max_repetitions)]
    for key in sorted(grouped_data):
        values = grouped_data[key]
        for i in range(max_repetitions):
            if i < len(values):
                output_rows[i].append(values[i])
            else:
                output_rows[i].append('')

    return output_rows



############search_scans routes change to questionaire codes

@app.route('/get_filtered_patient_codes', methods=['POST'])
def get_filtered_patient_codes():
    print("Received request for filtered patient codes")

    # Extract data from form
    start_date_of_scan = request.form.get('start_date_of_scan')
    end_date_of_scan = request.form.get('end_date_of_scan')
    start_hour_of_scan = request.form.get('start_hour_of_scan')
    end_hour_of_scan = request.form.get('end_hour_of_scan')
    study = request.form.get('study')
    group = request.form.get('group')
    Protocol = request.form.get('Protocol')
    scan_no = request.form.get('scan_no')
    gender = request.form.get('gender')
    age_from = request.form.get('age_from')
    age_to = request.form.get('age_to')
    height_from = request.form.get('height_from')
    height_to = request.form.get('height_to')
    weight_from = request.form.get('weight_from')
    weight_to = request.form.get('weight_to')
    Dominant_hand = request.form.get('Dominant_hand')

    # Extract protocol data
    protocols = {scan_type: request.form.get(scan_type) for scan_type in SCAN_TYPES}
    connection = connect_to_db()
    if connection:
        patient_codes = build_and_execute_query(connection, protocols,gender, age_from, age_to, start_date_of_scan, start_hour_of_scan, end_date_of_scan, end_hour_of_scan, weight_from, weight_to,height_from,height_to,' ',study,group,Protocol,scan_no,Dominant_hand,'yes','NULL')
        patient_codes.sort()
        print("Returning patient codes:", patient_codes)
        return jsonify(patient_codes)
    return jsonify([])

@app.route('/search_scans', methods=['GET', 'POST'])
def index():
    if session.get('authenticated'):
      connection = connect_to_db()
      if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT questionairecode FROM crf")
        patient_codes = [row[0] for row in cursor.fetchall()]
        patient_codes.sort()  # Sort patient codes alphabetically
        cursor.execute("SELECT DISTINCT groupname FROM crf where groupname <>'NULL' and groupname<>'nan'")
        group_names = [row[0] for row in cursor.fetchall()]
        group_names.sort()  # Sort patient codes alphabetically
        cursor.execute("SELECT DISTINCT Protocol FROM crf where Protocol <>'NULL' and Protocol<>'nan'")
        Protocols = [row[0] for row in cursor.fetchall()]
        Protocols.sort()  #
        cursor.execute("SELECT DISTINCT study FROM crf where study <>'NULL' and study<>'nan'")
        studies = [row[0] for row in cursor.fetchall()]
        studies.sort()
        cursor.execute("SELECT DISTINCT noscan FROM crf where noscan <>'NULL' and noscan<>'nan'")
        scan_numbers = [row[0] for row in cursor.fetchall()]
        scan_numbers.sort()
        cursor.execute("select distinct(answer) from answers where questioneid='5' and answer <>'nan'")
        Dominant_hand = [row[0] for row in cursor.fetchall()]
        Dominant_hand.sort()
        cursor.execute("SELECT * FROM questiones WHERE questioneid >= 14 AND questioneid <= 15")
        custom_questions = [row[1] for row in cursor.fetchall()]
        cursor.execute("SELECT * FROM questiones WHERE questioneid >= 23 AND questioneid <= 28")
        education_work_questions = [row[1] for row in cursor.fetchall()]
        cursor.execute("SELECT * FROM questiones WHERE questioneid >= 313 AND questioneid <= 329")
        music_questions = [row[1] for row in cursor.fetchall()]
        all_questions =custom_questions + education_work_questions + music_questions
        connection.close()
      if request.method == 'POST':
        selected_patient_codes = request.form.getlist('subjects[]')
        selected_types = {scan_type: request.form.get(scan_type) for scan_type in SCAN_TYPES}
        selected_genders = request.form.getlist('gender')
        age_from = request.form.get('age_from')
        age_to = request.form.get('age_to')
        start_date_of_scan = request.form.get('start_date_of_scan')
        start_hour_of_scan = request.form.get('start_hour_of_scan')
        end_date_of_scan = request.form.get('end_date_of_scan')
        end_hour_of_scan = request.form.get('end_hour_of_scan')
        weight_from = request.form.get('height_from')
        weight_to = request.form.get('height_to')
        height_from = request.form.get('height_from')
        height_to = request.form.get('height_to')
        Study = request.form.get('study')
        Group = request.form.get('group')
        Protocol = request.form.get('Protocol')
        scan_number = request.form.get('scan_no')
        selected_patient_codes = request.form.getlist('selected_patient_codes')
        Dominant_hand = request.form.getlist('Dominant_hand')
        connection = connect_to_db()
        if connection:
            all_columns = get_all_columns(connection, "scans")
            results = build_and_execute_query(connection, selected_types, selected_genders, age_from, age_to, start_date_of_scan, start_hour_of_scan, end_date_of_scan, end_hour_of_scan, weight_from,weight_to,height_from,height_to,selected_patient_codes, all_columns,Study,Group,Protocol,scan_number,Dominant_hand[0],'no','NULL')
            connection.close()

            if results:
                return render_template('results.html', columns=['path'], results=results, message=None)
            else:
                return render_template('results.html', columns=['path'], results=[], message="No data found.")

      return render_template('search_scans.html', scan_types=SCAN_TYPES, patient_codes=patient_codes,group_names=group_names,studies=studies,Protocols=Protocols,scan_numbers=scan_numbers,Dominant_hand=Dominant_hand,all_questions=all_questions)
    else:
        return render_template('loginPage.html')




@app.route('/export', methods=['POST'])
def export():
    # Get all the form data
    connection = connect_to_db()
    cursor = connection.cursor()
    file = request.files.get('file')
    selected_types = {}
    for scan_type in SCAN_TYPES:
        values = request.form.getlist(scan_type)
        if values:
            selected_types[scan_type] = values[0]
        else:
            selected_types[scan_type] = ''
    if request.form.getlist('gender'):
       selected_genders = request.form.getlist('gender')[0]
    else:
       selected_genders = request.form.getlist('gender')
    all_selected_questions = request.form.getlist('all_selected_questions_display')
    Dominant_hand=request.form.getlist('Dominant hand')
    age_from = request.form.get('age_from')
    age_to = request.form.get('age_to')
    start_date_of_scan = request.form.get('start_date_of_scan')
    start_hour_of_scan = request.form.get('start_hour_of_scan')
    end_date_of_scan = request.form.get('end_date_of_scan')
    end_hour_of_scan = request.form.get('end_hour_of_scan')
    weight_from = request.form.get('height_from')
    weight_to = request.form.get('height_to')
    height_from = request.form.get('height_from')
    height_to = request.form.get('height_to')
    Study = request.form.get('study')
    Group = request.form.get('group')
    Protocol = request.form.get('Protocol')
    scan_number = request.form.get('scan_no')
    selected_patient_codes = request.form.getlist('selected_patient_codes')
    if request.form.getlist('Dominant_hand'):
        Dominant_hand = request.form.getlist('Dominant_hand')[0]
    else:
        Dominant_hand = request.form.getlist('Dominant_hand')
    # Connect to the database and get results
    fields = ['Gender', 'crf.datetimescan', 'Ageofscan', 'weight', 'height', 'Study', 'Protocol','Group','bidspath','resultspath','rawdatapath']
    Data_output=[]
    # Iterate through each field
    Dominant_hand_post ='no'
    for field in fields:
        value = request.form.get(field)  # Get the value from the form
        if value and value != 'None':  # Check if it's not None or 'None'
            Data_output.append(value)  # Append to the output list

    connection = connect_to_db()
    if connection and selected_patient_codes:
        wb = Workbook()
        ws = wb.active
        ws.title = "Results"
        # Write headers
        headers = ["Subject"] + ["details"] + ["at"] + ["the"] + ["time"] + ["of"] + ["the"] + ["scan"]
        append_and_color_header(ws, headers, "FFFFFF00")
        headers = ["Questionaire Code"] + [column for column in Data_output]
        ws.append(headers)
        for code in selected_patient_codes:
            newcode=[]
            newcode.append(code)
            result = build_and_execute_query(connection, selected_types, selected_genders, age_from, age_to,
                                              start_date_of_scan, start_hour_of_scan, end_date_of_scan, end_hour_of_scan,
                                              weight_from, weight_to, height_from, height_to,newcode, Study, Group, Protocol, scan_number,Dominant_hand,'no',Data_output)

            if result:

                    cleaned_result = [item for value in result for item in flatten_values(clean_value(value))]
                    ws.append([code] + cleaned_result)

            # Create an Excel file in memory
        ws.append([])
        if Dominant_hand:
            all_selected_questions.append('')
        all_selected_questions_str = ", ".join(f"'{question}'" for question in all_selected_questions)
        query = f"""SELECT questioneid
                    FROM questiones
                    WHERE question IN ({all_selected_questions_str})
                 """
        print(query)
        cursor.execute(query)
        question_ids = cursor.fetchall()
        question_ids = ','.join(str(id[0]) for id in question_ids)
        headers = ["Subject"] + ["details"] + ["from"] + ["questionaire"]
        append_and_color_header(ws, headers, "FFFF0000")
        headers = ["Questionaire Code"] + [question for question in all_selected_questions]
        ws.append(headers)
        for code in selected_patient_codes:
                query = f""" SELECT answers.questioneid,answers.answer
                             FROM subjects inner join answers on subjects.questionairecode=answers.questionairecode
                             WHERE subjects.questionairecode = ('{code}') and answers.questioneid IN ({question_ids})
                       """
                cursor.execute(query)
                result = cursor.fetchall()
                keys = [item[0] for item in result]
                question_ids_temp = re.findall(r'\d+', question_ids)
                # Convert the extracted strings to integers
                question_ids_temp = [int(num) for num in question_ids_temp]
                for question_id_temp in question_ids_temp:
                    if question_id_temp not in keys:
                        result.append((question_id_temp, 'Nan'))
                processed_data = process_flexible_data(headers, code, result)
                for data in processed_data:
                    ws.append(data)

        excel_file = BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='results.xlsx'
        )

    return Response("No data found or an error occurred", status=400)
########## filter1
# @app.route('/', methods=['GET', 'POST'])
# def filter_page():
#     # Example data for locations
#     locations = ["New York", "Los Angeles", "Chicago", "Miami"]
#
#     # Existing context data
#     return render_template('search_scans.html', all_questions=locations)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files and 'additionalDetails' not in request.form and 'selectedQuestions' not in request.form:
        return jsonify({'error': 'No file, data, or selected questions provided'})
    detail_type = request.form.get('detailType')


    file = request.files.get('file')
    data_text = request.form.get('additionalDetails')
    selected_questions = json.loads(request.form.get('selectedQuestions', '[]'))

    codes_array = []

    if file and file.filename:
        try:
            file_content = file.read()
            if file.filename.endswith('.csv'):
                df = pd.read_csv(io.StringIO(file_content.decode('utf-8')))
            elif file.filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                return jsonify({'error': 'Unsupported file format'})

            codes_array = df.values.flatten().tolist()
            # Regular expression pattern for matching paths or IDs
            pattern = re.compile(r'^([A-Za-z]:?(?:[\w-]+[/\\])*[\w-]+|[A-Za-z0-9_]+|[A-Za-z0-9]{6,})$')

            codes_array = [
                code for code in codes_array
                if (isinstance(code, str) and pattern.match(code)) or
                   (isinstance(code, (int, float)) and not pd.isna(code) and pattern.match(str(code)))
            ]
            if 'Uploaded' in codes_array:
                codes_array=codes_array[:-3]



        except Exception as e:
            return jsonify({'error': str(e)})

    elif data_text and len(codes_array)==0:
        codes_array.extend(data_text.split())

    elif not codes_array:
        return jsonify({'error': 'No valid patient codes provided'})

    elif not selected_questions:
        return jsonify({'error': 'No questions selected'})

    conn = connect_to_db()
    if not conn:
        return jsonify({'error': 'Unable to connect to the database'})

    try:
        with (conn.cursor() as cur):
            crf_columns = ['groupname', 'Ageofscan', 'gender', 'scanno','datetimescan', 'height', 'weight', 'study', 'Protocol','scanfile']
            question_ids = ', '.join(f"'{qid}'" for qid in selected_questions if qid not in crf_columns)

            if question_ids!="":
              cur.execute(f"SELECT questioneid, question FROM questiones WHERE questioneid IN ({question_ids})")
              categories = cur.fetchall()



            # Fetch answers
            results = {}
            answer_columns=['questioneid','answer']
            answer_questionsids = [str(i) for i in range(1, 501)]
            select_columns=[]
            left_joins = []
            flag=0
            headers = ["Patient Code"]
            for column in crf_columns:
                if column in selected_questions:
                    if column=='datetimescan' and detail_type=='pathScanFile':
                       select_columns.append(f"crf.{column}")
                    else:
                       select_columns.append(f"{column}")
                    headers=headers+[column]
            if detail_type=='questionairecode' or detail_type=='pathScanFile':
            # Create Excel file
              wb = Workbook()
              ws = wb.active
              ws.title = "Results"
              # Write headers
              headers = ["Patient Code"] + [qid for qid in selected_questions if qid in crf_columns]
              conn = connect_to_db()
              with conn.cursor() as cur:
                if select_columns:
                  ws.append([""])
                  select_columns_str = ", ".join(select_columns)
                  headers=["Subject"]+["details"]+["at"]+["the"]+["time"]+["of"]+["the"]+["scan"]
                  append_and_color_header(ws, headers, "FFFFFF00")
                  ws.append([""])
                  ws.append([""])
                  if detail_type=='subjectId':
                    headers=["Subject ID"]+select_columns
                    ws.append(headers)
                  elif detail_type=='pathScanFile':
                    headers = ["Path Scan File"] + select_columns
                    ws.append(headers)
                  if detail_type=='subjectId':
                    for code in codes_array:
                      query = f""" SELECT {select_columns_str}
                                   FROM subjects inner join crf on subjects.questionairecode=crf.questionairecode
                                   WHERE subjects.questionairecode = ('{code}')
                               """
                      cur.execute(query)
                      result = cur.fetchone()
                      if result:
                          cleaned_result = [clean_value(value) for value in result]
                          ws.append([code]+cleaned_result)
                  elif detail_type=='pathScanFile':
                      for code in codes_array:
                          query = f""" SELECT {select_columns_str}
                                       FROM subjects inner join crf on subjects.questionairecode=crf.questionairecode inner join scans on crf.datetimescan=scans.datetimescan
                                       WHERE scans.rawdatapath = ('{code}')
                                 """
                          cur.execute(query)
                          result = cur.fetchone()
                          if result:
                              cleaned_result = [clean_value(value) for value in result]
                              ws.append([code] + cleaned_result)
                if question_ids!="":
                   cur.execute(f""" SELECT questioneid,question
                                    from questiones
                                    where questioneid IN ({question_ids}) order by questioneid""")
                   questions = cur.fetchall()
                   ws.append([""])
                   headers = ["Subject"] + ["details"] + ["from"] + ["questionaire"]
                   append_and_color_header(ws, headers, "FFFF0000")

                   result=""
                   if detail_type == 'subjectId':
                     headers = ["Subject ID"] + [question[1] for question in questions]
                     ws.append([""])
                     ws.append([""])
                     ws.append(headers)
                     for code in codes_array:
                       query = f""" SELECT answers.questioneid,answers.answer
                                    FROM subjects inner join answers on subjects.questionairecode=answers.questionairecode
                                    WHERE subjects.questionairecode = ('{code}') and answers.questioneid IN ({question_ids})
                                """
                       cur.execute(query)
                       result = cur.fetchall()
                       keys = [item[0] for item in result]
                       question_ids_temp = re.findall(r'\d+', question_ids)
                       # Convert the extracted strings to integers
                       question_ids_temp = [int(num) for num in question_ids_temp]
                       for question_id_temp in question_ids_temp:
                           if question_id_temp not in keys:
                               result.append((question_id_temp, 'Nan'))
                       processed_data = process_flexible_data(headers, code, result)
                       for data in processed_data:
                           ws.append(data)
                   elif detail_type == 'pathScanFile':
                     headers = ["Path Scan File"] + [question[1] for question in questions]
                     ws.append([""])
                     ws.append([""])
                     ws.append(headers)
                     for code in codes_array:
                        query = f""" SELECT answers.questioneid,answers.answer
                                        FROM subjects inner join answers on subjects.questionairecode=answers.questionairecode
                                        inner join crf on subjects.questionairecode=crf.questionairecode inner join scans on crf.datetimescan=scans.datetimescan
                                        WHERE scans.rawdatapath = ('{code}') and answers.questioneid IN ({question_ids})
                                    """
                        cur.execute(query)
                        result = cur.fetchall()
                        keys = [item[0] for item in result]
                        question_ids_temp = re.findall(r'\d+', question_ids)

# Convert the extracted strings to integers
                        question_ids_temp = [int(num) for num in question_ids_temp]
                        for question_id_temp in question_ids_temp:
                          if question_id_temp not in keys:
                              result.append((question_id_temp, 'Nan'))
                        processed_data=process_flexible_data(headers, code, result)
                        for data in processed_data:
                            ws.append(data)
                        ws.append(processed_data)
              excel_file = BytesIO()
              wb.save(excel_file)
              excel_file.seek(0)
              return send_file(
                      excel_file,
                      mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                      as_attachment=True,
                      download_name='results.xlsx'
              )
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return jsonify({'error': 'Database error occurred while processing questions'})
    finally:
        if conn:
            conn.close()


@app.route('/get_questions', methods=['GET'])
def get_questions():
    category = request.args.get('category')
    category_index_ranges = {
        'דמוגרפי כללי': [(3, 13)],
        'שפה ושיוך': [(14, 17)],
        'מצב משפחתי': [(17, 22)],
        'השכלה ומקצוע': [(23, 28)],
        'תחביבים והעדפות': [(29, 32), (464, 481), (489, 499)],
        'אורח חיים ועמדות': [(33, 47), (299, 312), (461, 464), (484, 484)],
        'שאלון שינה': [(48, 73)],
        'מצב בריאותי': [(74, 207), (290, 298)],
        'שאלון אישיות': [(208, 255)],
        'שאלון פסיכומטרי': [(256, 264)],
        'שאלון חרדה': [(265, 269)],
        'שאלון פוביות': [(270, 277)],
        'שאלון צאצאים שורדי שואה': [(278, 289)],
        'שאלון מוזיקה': [(313, 329)],
        'שאלון תכנות': [(330, 339)],
        'שאלון סמארטפון': [(340, 368)],
        'שאלון דיכאון וחרדה': [(369, 386)],
        'שאלון פוסט טראומה': [(387, 434)],
        'שאלון שבעה באוקטובר': [(435, 460)],
        'שאלות סיום': [(482, 483)],
        'All the questions': [(3, 501)],
    }

    conn = connect_to_db()
    if not conn:
        return jsonify({'error': 'Unable to connect to the database'})

    try:
        with conn.cursor() as cur:
            if category == 'Most_common_questions':
                common_questions = [
                    ('gender', 'Gender (at the time of the scan)'),
                    ('datetimescan', 'Date and time of scan'),
                    ('Ageofscan', 'Ageofscan (at the time of the scan)'),
                    ('weight', 'Weight (kg) (at the time of the scan)'),
                    ('height', 'Height (cm) (at the time of the scan)'),
                    ('study', 'study'),
                    ('Protocol', 'Protocol'),
                    ('groupname', 'Group'),
                    ('4', 'Dominant hand'),
                    #('Scan Details', 'Scan Details')
                ]
                cur.execute("SELECT * FROM questiones WHERE questioneid >= 14 AND questioneid <= 15")
                custom_questions = cur.fetchall()
                cur.execute("SELECT * FROM questiones WHERE questioneid >= 23 AND questioneid <= 28")
                education_work_questions = cur.fetchall()
                cur.execute("SELECT * FROM questiones WHERE questioneid >= 313 AND questioneid <= 329")
                music_questions = cur.fetchall()

                all_questions = common_questions + custom_questions + education_work_questions + music_questions
                return jsonify({'questions': all_questions})
            elif category == 'subject_details_at_the_time_of_scan':
                patient_details = [
                    ('gender', 'Gender (at the time of the scan) '),
                    ('datetimescan', 'Date and time of scan'),
                    ('Ageofscan', 'Ageofscan (at the time of the scan)'),
                    ('weight', 'Weight (kg) (at the time of the scan)'),
                    ('height', 'Height (cm) (at the time of the scan)'),
                    ('study', 'study'),
                    ('Protocol', 'Protocol'),
                    ('groupname', 'Group'),
                    # ('Scan Details', 'Scan Details')
                ]
                return jsonify({'questions': patient_details})
            elif category in category_index_ranges:
                questions = []
                for start_index, end_index in category_index_ranges[category]:
                    cur.execute("SELECT * FROM questiones WHERE questioneid >= %s AND questioneid <= %s",
                                (start_index, end_index))
                    questions.extend(cur.fetchall())
                return jsonify({'questions': questions})
            else:
                return jsonify({'error': 'Invalid category'})
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return jsonify({'error': 'Database error occurred'})
    finally:
        if conn:
            conn.close()


@app.route('/')
def index2():
    session['authenticated'] = False
    return render_template('loginPage.html')

@app.route('/login', methods=['POST'])
def login():

    password = request.form['password']
    if password == "asgard2014":  # Example check
        session['authenticated'] = True
        return redirect(url_for('OptionPage'))
    else:
        flash('Incorrect password. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/Get_additinal_information')
def filters1():
    if session.get('authenticated'):
        return render_template('Get_additinal_information.html')
    else:
        return render_template('loginPage.html')


@app.route('/HomePage')
def OptionPage():
    if session.get('authenticated'):
        return render_template('HomePage.html')
    else:
        return render_template('loginPage.html')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run()