import numpy as np
import pandas as pd
from flask import request

"""
Class which should wait to receive the records
in this case loads the data from csv files
"""


class RecordReceiver:
    record_required_keys = {"UUID", "player_id", "device"}
    medical_sample_required_keys = {"days_missed", "games_missed"}
    social_sample_required_keys = {"number_of_likes", "number_of_followers"}
    stats_sample_required_keys = {"overall"}
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
    
    def receive_record(self):
        """
        receive a post request validate the json schema and convert to pandas dataframe
        """
        record = request.get_json()

        if not self.validate_json_schema(record):

            return None,None
        
        for key, value in record.items():
            if value is None or value == "":
                record[key] = np.nan

        df = pd.DataFrame(record, index=[0])

        df = df.map(lambda x: None if pd.isnull(x) else x)

        table = None

        if "label" in record:
            table = "labels"
        elif "day_missed" in record:
            table = "medical"
        elif "overall" in record:
            table = "football"
        elif "number_of_likes" in record:
            table = "social"

        return df, table
        

        
        
    

    
