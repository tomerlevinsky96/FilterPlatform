import psycopg2
from Configuration import DB_CONFIG, COLUMN_MAPPING
from psycopg2 import Error
from datetime import datetime


class search_values:
    # Define class attributes
    _instance = None  # This will hold the single instance
    update_subjects = None
    connection = None
    Dominant_hand = None
    Dominant_hand_post = None
    scan_id=None
    path=None
    db_column= None
    number_of_scans=None
    additinal_information=None
    def __init__(self):
        # Initialize instance attributes if not already initialized

        if not hasattr(self, 'Data_output'):
            self.Data_output = []
        if not hasattr(self, 'query_values'):
            self.query_values = {
                'age_from': None,\
                'age_to': None, \
                'start_date_of_scan': None, \
                'start_hour_of_scan': None, \
                'end_date_of_scan': None, \
                'end_hour_of_scan': None, \
                'weight_from': None, \
                'weight_to': None, \
                'height_from': None, \
                'height_to': None, \
                'selected_patient_codes': None, \
                'Study': None, \
                'Group': None, \
                'Protocol': None, \
                'scan_number': None, \
                'selected_types': None, \
                'selected_genders': None, \
                'kepreppath':None, \
                'kepostpath':None, \
                'freesurferpath':None,\
                'scanid':None,\
            }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(search_values, cls).__new__(cls)
        return cls._instance
    def connect_to_db(self):
        try:
            connection = psycopg2.connect(**DB_CONFIG)
            connection.autocommit = True
            return connection
        except Error as e:
            print(f"Error while connecting to PostgreSQL: {e}")
            return None

    # Individual getter and setter methods for each attribute

    @classmethod
    def get_instance(cls):
        return cls._instance or cls()

    def set_additinal_information(self, value):
        self.additinal_information = value

    def get_additinal_information(self, value):
        return self.additinal_information


    def get_age_from(self):
        return self.query_values['age_from']

    def set_number_of_scans(self, value):
        self.query_values['questionaire_category'] = value

    def get_number_of_scans(self, value):
        return self.query_values['questionaire_category']


    def set_number_of_scans(self, value):
        self.number_of_scans = value

    def get_number_of_scans(self):
        return self.number_of_scans

    def set_age_from(self, value):
        self.query_values['age_from'] = value

    def get_age_to(self):
        return self.query_values['age_to']

    def set_age_to(self, value):
        self.query_values['age_to'] = value

    def get_start_date_of_scan(self):
        return self.query_values['start_date_of_scan']

    def set_start_date_of_scan(self, value):
        self.query_values['start_date_of_scan'] = value

    def get_start_hour_of_scan(self):
        return self.query_values['start_hour_of_scan']

    def set_start_hour_of_scan(self, value):
        self.query_values['start_hour_of_scan'] = value

    def get_end_date_of_scan(self):
        return self.query_values['end_date_of_scan']

    def set_end_date_of_scan(self, value):
        self.query_values['end_date_of_scan'] = value

    def get_end_hour_of_scan(self):
        return self.query_values['end_hour_of_scan']

    def set_end_hour_of_scan(self, value):
        self.query_values['end_hour_of_scan'] = value

    def get_weight_from(self):
        return self.query_values['weight_from']

    def set_weight_from(self, value):
        self.query_values['weight_from'] = value

    def get_weight_to(self):
        return self.query_values['weight_to']

    def set_weight_to(self, value):
        self.query_values['weight_to'] = value

    def get_height_from(self):
        return self.query_values['height_from']

    def set_height_from(self, value):
        self.query_values['height_from'] = value

    def get_height_to(self):
        return self.query_values['height_to']

    def set_height_to(self, value):
        self.query_values['height_to'] = value

    def get_selected_patient_codes(self):
        return self.query_values['selected_patient_codes']

    def set_selected_patient_codes(self, value):
        self.query_values['selected_patient_codes']=value

    def set_selected_scanids(self, value):
        self.query_values['scanid'] = value

    def get_study(self):
        return self.query_values['Study']

    def set_study(self, value):
        self.query_values['Study'] = value

    def get_group(self):
        return self.query_values['Group']

    def set_group(self, value):
        self.query_values['Group'] = value

    def get_protocol(self):
        return self.query_values['Protocol']

    def set_protocol(self, value):
        self.query_values['Protocol'] = value

    def get_scan_number(self):
        return self.query_values['scan_number']

    def set_scan_number(self, value):
        self.query_values['scan_number'] = value

    def get_dominant_hand(self):
        return self.Dominant_hand

    def set_dominant_hand(self, value):
        self.Dominant_hand = value

    def get_dominant_hand_post(self):
        return self.Dominant_hand_post

    def set_dominant_hand_post(self, value):
        self.Dominant_hand_post = value

    def get_update_subjects(self):
        return self.update_subjects

    def set_update_subjects(self, value):
        self.update_subjects = value

    def get_data_output(self):
        return self.Data_output

    def get_selected_types(self):
        return self.query_values['selected_types']

    def set_selected_types(self, value):
        self.query_values['selected_types'] = value

    def get_selected_genders(self):
        return self.query_values['selected_genders']

    def set_selected_genders(self, value):
        self.query_values['selected_genders'] = value

    def get_connection(self):
        return self.connection

    def set_connection(self, value):
        self.connection = value

    def append_to_data_output(self, value):
        if value not in ['None', 'Dominant.hand']:
            if self.Data_output is None:
                self.Data_output = []
            self.Data_output.append(value)

    def get_distinct_values(self, columns):
        try:
            cursor = self.connection.cursor()
            sql_column_name = COLUMN_MAPPING.get(columns)
            if sql_column_name is None:
                print(f"No mapping found for column: {columns}")
                return []

            query = f"SELECT DISTINCT {sql_column_name} FROM scans"
            cursor.execute(query)

            values = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return values
        except Error as e:
            print(f"Error fetching distinct values for {columns}:", e)
            return []

    def build_and_execute_query(self):
        where_conditions = []
        params = []
        include_scans = 'no'
        # Process selected types
        where_protocol_condition=[]
        if self.query_values['selected_types']:
         for scan_type, value in self.query_values['selected_types'].items():
            db_column = COLUMN_MAPPING.get(scan_type)
            if db_column:
                if str(value) != 'None':
                    if value.lower() == 'ok':
                        include_scans = 'yes'
                        # Search for distinct values of the column
                        distinct_values = search_values.get_instance().get_distinct_values(scan_type)
                        # If 'OK' is one of the distinct values, add it to the search condition
                        for value in distinct_values:
                            if value is not None and value.lower() not in ['failed', 'none']:
                                where_protocol_condition.append(f"{db_column} = '{value}'")
        if len(where_protocol_condition)>0:
            where_protocol_condition= f"({' OR '.join(where_protocol_condition)})" if where_protocol_condition else ""
            where_conditions.append(where_protocol_condition)



        # Process selected genders
        if self.query_values['selected_genders']:
            gender_condition = f"gender IN ('{self.query_values['selected_genders']}')"
            where_conditions.append(gender_condition)
        # Process age range
        if self.query_values['age_from']:
            where_conditions.append(
                f"Ageofscan ~ '^[0-9]*\.?[0-9]+$' and  CAST(Ageofscan AS NUMERIC)>= '{self.query_values['age_from']}'")
        if self.query_values['age_to']:
            where_conditions.append(
                f"Ageofscan ~ '^[0-9]*\.?[0-9]+$' and  CAST(Ageofscan AS NUMERIC)<= '{self.query_values['age_to']}'")
        if self.query_values['weight_from']:
            where_conditions.append(f"weight ~ '^[0-9]*\.?[0-9]+$' and CAST(weight AS NUMERIC)>='{self.query_values['weight_from']}'")
        if self.query_values['weight_to']:
            where_conditions.append(f"weight ~ '^[0-9]*\.?[0-9]+$' and CAST(weight AS NUMERIC)<='{self.query_values['weight_to']}'")
        if self.query_values['height_from']:
            where_conditions.append(f"height ~ '^[0-9]*\.?[0-9]+$' and CAST(height AS NUMERIC)>= '{self.query_values['height_from']}'")
        if self.query_values['height_to']:
            where_conditions.append(f"height ~ '^[0-9]*\.?[0-9]+$' and CAST(height AS NUMERIC)<= '{self.query_values['height_to']}'")
        if self.query_values['Study']:
            where_conditions.append(f"study = '{self.query_values['Study']}'")
        if self.query_values['Group']:
            where_conditions.append(f"groupname = '{self.query_values['Group']}'")
        if self.query_values['Protocol']:
            where_conditions.append(f"protocol = '{self.query_values['Protocol']}'")
        if self.query_values['scan_number']:
            where_conditions.append(f"noscan = '{self.query_values['scan_number']}'")
        if self.Dominant_hand:
            where_conditions.append(f"answer = '{self.Dominant_hand}'")





        if self.query_values['start_date_of_scan'] and self.query_values['end_date_of_scan'] and self.query_values['start_hour_of_scan'] and self.query_values['end_hour_of_scan']:
            # If all date and time filters are present
            where_conditions.append(
                f"crf.datetimescan::date BETWEEN '{self.query_values['start_date_of_scan']}' AND '{self.query_values['end_date_of_scan']}' AND "
                f"crf.datetimescan::time BETWEEN '{self.query_values['start_hour_of_scan']}' AND '{self.query_values['end_hour_of_scan']}'"
            )

        elif self.query_values['start_date_of_scan'] and self.query_values['end_date_of_scan']:
            # If only date filters are present
            where_conditions.append(
                f"crf.datetimescan::date BETWEEN '{self.query_values['start_date_of_scan']}' AND '{self.query_values['end_date_of_scan']}'"
            )

        elif self.query_values['start_date_of_scan'] and not self.query_values['end_date_of_scan'] and self.query_values['start_hour_of_scan'] and self.query_values['end_hour_of_scan']:
            # If start date and time filters are present
            where_conditions.append(
                f"crf.datetimescan::date >= '{self.query_values['start_date_of_scan']}' AND "
                f"crf.datetimescan::time BETWEEN '{self.query_values['start_hour_of_scan']}' AND '{self.query_values['end_hour_of_scan']}'"
            )

        elif self.query_values['end_date_of_scan'] and not self.query_values['start_date_of_scan'] and self.query_values['start_hour_of_scan']  and self.query_values['end_hour_of_scan']:
            # If end date and time filters are present
            where_conditions.append(
                f"crf.datetimescan::date <= '{self.query_values['end_date_of_scan']}' AND "
                f"crf.datetimescan::time BETWEEN '{self.query_values['start_hour_of_scan']}' AND '{self.query_values['end_hour_of_scan']}'"
            )

        elif self.query_values['start_hour_of_scan'] and self.query_values['end_hour_of_scan']:
            # If only time filters are present
            where_conditions.append(
                f"crf.datetimescan::time BETWEEN '{self.query_values['start_hour_of_scan']}' AND '{self.query_values['end_hour_of_scan']}'"
            )

        elif self.query_values['start_date_of_scan']:
            # If only start date is present
            where_conditions.append(f"crf.datetimescan::date >= '{self.query_values['start_date_of_scan']}'")

        elif self.query_values['end_date_of_scan']:
            # If only end date is present
            where_conditions.append(f"crf.datetimescan::date <= '{self.query_values['end_date_of_scan']}'")

        # Process selected patient codes
        if self.update_subjects == 'no':
            if self.query_values['selected_patient_codes']:
                patient_condition = f"subjects.questionairecode IN ({', '.join(map(repr, self.query_values['selected_patient_codes']))})"
                where_conditions.append(patient_condition)
            elif self.query_values['scanid']:
                patient_condition = f"crf.scanid IN ({', '.join(map(repr, self.query_values['scanid']))})"
                where_conditions.append(patient_condition)



        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

        if self.additinal_information=='yes':
            where_clause=f"""WHERE crf.guid IN (SELECT guid FROM crf WHERE crf.questionairecode IN ({', '.join(map(repr, self.query_values['selected_patient_codes']))}))"""


        if self.update_subjects == 'yes':
            columns = f"""distinct(crf.questionairecode)"""
            where_clause=where_clause+f" And subjects.questionairecode IS NOT NULL AND subjects.questionairecode <> '' and subjects.questionairecode<>'nan'"
        if self.update_subjects == 'no':
            columns='crf.scanid,crf.guid,crf.questionairecode'
            columns =columns+','+ ', '.join(column.strip("'") for column in self.Data_output)


        if self.Dominant_hand or self.Dominant_hand_post != 'no':
            query = f"""
                        SELECT {columns}
                        FROM subjects inner join crf on subjects.questionairecode=crf.questionairecode left join answers on subjects.questionairecode=answers.questionairecode AND answers.questioneid = '4'
                        left JOIN scans ON crf.datetimescan = scans.datetimescan 
                        {where_clause} Group by {columns}
                       """
        elif self.Dominant_hand_post != 'no':
            query = f"""
                                SELECT {columns}
                                FROM subjects inner join crf on subjects.questionairecode=crf.questionairecode left join answers on subjects.questionairecode=answers.questionairecode AND answers.questioneid = '4'
                                left JOIN scans ON crf.datetimescan = scans.datetimescan 
                                {where_clause} Group by {columns}
                               """
        elif include_scans == 'yes':
            query = f"""
                        SELECT {columns}
                        FROM subjects inner join crf on subjects.questionairecode=crf.questionairecode 
                        left JOIN scans ON crf.datetimescan = scans.datetimescan 
                        {where_clause} Group by {columns}
                    """


        else:
            query = f"""
                        SELECT {columns}
                        FROM subjects inner join crf on subjects.questionairecode=crf.questionairecode
                        {where_clause} Group by {columns}
                        """

        try:
            cursor = self.connection.cursor()
            full_query = cursor.mogrify(query, params).decode('utf-8')
            if self.number_of_scans == 'one' and self.update_subjects == 'yes':
                full_query = full_query + f" having count(scanid)=1"

            if self.number_of_scans == 'more than one' and self.update_subjects == 'yes':
                full_query = full_query + f" having count(scanid)>1"

            print("Full query:", full_query)
            cursor.execute(full_query)
            results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"Error executing query: {e}")
            return None
    def insert_keprep_path(self,scan_id,path):
        self._insert_data_path(scan_id,path,'kepreppath')
    def insert_keppost_path(self,scan_id,path):
        self._insert_data_path(scan_id,path,'kepostpath')
    def insert_freesurfer_path(self,scan_id,path):
        self._insert_data_path(scan_id,path,'freesurferpath')

    def _insert_data_path(self, scan_id,path,db_column):
        self.set_connection(self.get_instance().connect_to_db())
        cursor = self.connection.cursor()
        if db_column=='kepreppath':
            update_query = f"""UPDATE scans SET kepreppath='{path}' where datetimescan='{scan_id}';"""
            cursor.execute(update_query)
            self.connection.commit()

        elif db_column=='kepostpath':
            update_query = f"""UPDATE scans SET kepostpath='{path}' where datetimescan='{scan_id}';"""
            cursor.execute(update_query)
            self.connection.commit()
            
        elif db_column=='freesurferpath':
            update_query = f"""UPDATE scans SET freesurferpath='{path}' where datetimescan='{scan_id}';"""
            cursor.execute(update_query)
            self.connection.commit()
        elif db_column=='bids':
            update_query = f"""UPDATE scans SET bidspath='{path}' where datetimescan='{scan_id}';"""
            cursor.execute(update_query)
            self.connection.commit()
    def _get_formated_values(self,result):
       values=[]
       for row in result:
           # Format each element in the row if it is a datetime
           formatted_row = tuple(
               element.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] if isinstance(element, datetime) else element
               for element in row
           )
           values.append(formatted_row)
       return values



    def _get_values(self,ids,get_by,db_column):
        self.set_connection(self.get_instance().connect_to_db())
        cursor = self.connection.cursor()
        values = []
        if db_column != 'dominant_hand' and 'path' not in db_column:
            select_query = f"SELECT {db_column}, {get_by} FROM crf WHERE {get_by} IN ({', '.join(map(repr, ids))})"
            cursor.execute(select_query)
            result=cursor.fetchall()
            result=self._get_formated_values(result)
        elif db_column == 'dominant_hand' :
            select_query = f"SELECT answers.answer,crf.{get_by} FROM subjects inner join crf on subjects.questionairecode=crf.questionairecode left join answers on subjects.questionairecode=answers.questionairecode AND answers.questioneid = '4' left JOIN scans ON crf.datetimescan = scans.datetimescan WHERE crf.{get_by} IN ({', '.join(map(repr, ids))})"
            cursor.execute(select_query)
            result = cursor.fetchall()
            result = self._get_formated_values(result)
        elif 'path' in db_column:
            select_query =f"select {db_column},CRF.{get_by} FROM subjects inner join crf on subjects.questionairecode=crf.questionairecode  left JOIN scans ON crf.datetimescan = scans.datetimescan WHERE CRF.{get_by} IN ({', '.join(map(repr, ids))})"
            cursor.execute(select_query)
            result = cursor.fetchall()
            result = self._get_formated_values(result)
        return result

    def set_kepreppath(self, value):
       self.query_values['kepreppath'] = value
    def set_kepostpath(self, value ):
        self.query_values['kepostpath'] = value
    def set_freesurferpath(self, value ):
        self.query_values['freesurferpath'] = value



    def get_age_values(self,scan_ids,get_by):
        return self._get_values(scan_ids,get_by,'ageofscan')
    def get_height_values(self,scan_ids,get_by):
        return self._get_values(scan_ids,get_by,'height')
    def get_weight_values(self,scan_ids,get_by):
        return self._get_values(scan_ids,get_by,'weight')
    def get_group_values(self,scan_ids,get_by):
        return self._get_values(scan_ids,get_by,'groupname')
    def get_protocol_values(self,scan_ids,get_by):
        return self._get_values(scan_ids,get_by,'protocol')
    def get_study_values(self,scan_ids,get_by):
        return self._get_values(scan_ids,get_by,'study')
    def get_scanid_values(self,scan_ids,get_by):
        return self._get_values(scan_ids,get_by,'datetimescan')

    def get_dominant_hand_values(self,scan_ids,get_by):
        return self._get_values(scan_ids,get_by,'dominant_hand')

    def get_bids_path_values(self,scan_ids,get_by):
        return self._get_values(scan_ids,get_by,'bidspath')

    def get_raw_data_path_values(self, scan_ids, get_by):
        return self._get_values(scan_ids, get_by, 'rawdatapath')

    def get_result_path_values(self,scan_ids,get_by):
        return self._get_values(scan_ids,get_by,'resultspath')

    def get_freesurfer_path_values(self,scan_ids,get_by):
        return self._get_values(scan_ids,get_by,'freesurferpath')
    def get_kepost_path_values(self,scan_ids,get_by):
        return self._get_values(scan_ids,get_by,'kepostpath')
    def get_keprep_path_values(self,scan_ids,get_by):
        return self._get_values(scan_ids,get_by,'kepreppath')
















