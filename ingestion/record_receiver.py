import numpy as np
import pandas as pd
from flask import request
import json
from pathlib import Path
from jsonschema import validate, ValidationError

"""
Class which should wait to receive the records
in this case loads the data from csv files
"""


class RecordReceiver:

    
    def __init__(self,schema_path : str):
         
        try:
            schema_path = Path(__file__).resolve().parents[0] / schema_path
            
            with schema_path.open(encoding="utf-8") as f:
                # We just load the entire JSON file as our schema
                self.schema = json.load(f) 

            print("[INFO] JSON Schema correctly loaded")

        except FileNotFoundError:
            print("ERROR> Record receiver : JSON schema file not found")
            raise
        except json.JSONDecodeError:
            print("ERROR> Record receiver : Error decoding json file")
            raise

    def validate_json_schema(self, record: dict) -> bool:

        try:
            # The bouncer: compares the record against the loaded schema
            validate(instance=record, schema=self.schema)

            return True
            
        except ValidationError as e:
            # If it fails, the library tells us exactly why 
            
            print(f"[INFO] Validation failed: {e.message}")

            return False
    
    def clean_json(self,record: dict) -> bool:
        #Clean the columns
        #remove all the unexpected columns
        allowed_keys = self.schema.get("properties", {}).keys()

        cleaned_dict = {key: value for key, value in record.items() if key in allowed_keys}

        return cleaned_dict

    
    def receive_record(self):
        """
        receive a post request validate the json schema and convert to pandas dataframe
        """
        record = request.get_json()

        #print(f"Record received: \n{record}")

        record=self.clean_json(record)

        #print(f"Record cleaned: \n{record}")

        if not self.validate_json_schema(record):

            return None
        
        
        
        for key, value in record.items():
            if value is None or value == "":
                record[key] = np.nan

        df = pd.DataFrame(record, index=[0])

        df = df.map(lambda x: None if pd.isnull(x) else x)

        return df
        

        
        
    

    
