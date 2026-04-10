import numpy as np
import pandas as pd
from flask import request

"""
Class which should wait to receive the records
in this case loads the data from csv files
"""


class RecordReceiver:
    record_required_keys = {"player_id"}
    medical_sample_required_keys = {"days_missed", "games_missed"}
    social_sample_required_keys = {"number_of_likes", "number_of_followers"}
    stats_sample_required_keys = {"skill_overall"}
    sample_label_required_keys = {"label"}

    def __init__(self):
        self.record_counter=0

    def validate_json_schema(self, record: dict) -> bool:
        
        record_check_passed = self.record_required_keys.issubset(record.keys()) or \
                              self.medical_sample_required_keys.issubset(record.keys()) or \
                              self.social_sample_required_keys.issubset(record.keys())  or \
                              self.stats_sample_required_keys.issubset(record.keys()) or \
                              self.sample_label_required_keys.issubset(record.keys())
        if not record_check_passed:
            return False
        
        return True
    
    def clean_json(self,record: dict) -> bool:
        #Clean the columns
        #remove all the unexpected columns
        keys_to_keep = ["player_id", "days_missed", "games_missed","number_of_likes","number_of_followers","skill_overall","label"]

        cleaned_dict = {key: value for key, value in record.items() if key in keys_to_keep}

        return cleaned_dict

    
    def receive_record(self):
        """
        receive a post request validate the json schema and convert to pandas dataframe
        """
        record = request.get_json()

        if not self.validate_json_schema(record):

            return None
        
        record=self.clean_json(record)
        
        for key, value in record.items():
            if value is None or value == "":
                record[key] = np.nan

        df = pd.DataFrame(record, index=[0])

        df = df.map(lambda x: None if pd.isnull(x) else x)

        return df
        

        
        
    

    
