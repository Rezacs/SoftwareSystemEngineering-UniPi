import json
from pathlib import Path

import pandas as pd
from flask import request
from jsonschema import validate, ValidationError


class RecordReceiver:
    """
    Used to get the json inputs from the client side system
    validate them and remove all the unexpected information

    Attributes:
         schema (json) : the json schema to refer, for validating an input
    """

    def __init__(self, schema_path: str):
        """Initializes the RecordsBuffer with a specified capacity.

           Args:
               schema_path (str): The path to the json schema used for input validation

           Raises :
               FileNotFoundError : if the json schema file is not found
               JSONDecodeError : if any problem decoding the json file occur
        """

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
        """
        This method is used to validate the schema of the received record

        Args:
          record (dict) : the record received

        Returns:
            bool : True if valid otherwise False

        Raises:
            ValidationError : if the received record has an invalid schema

        """

        try:
            # The bouncer: compares the record against the loaded schema
            validate(instance=record, schema=self.schema)

            return True

        except ValidationError as e:
            # If it fails, the library tells us exactly why
            print(f"[INFO] Validation failed: {e.message}")

            return False

    def clean_json(self, record: dict) -> dict:
        """
        This method is used to remove all the unexpected info inside the record

        Args:
          record (dict) : the received record

        Returns:
            cleaned_dict (dict) : the record without all the unexpected data

        """
        # Clean the columns
        # remove all the unexpected columns
        allowed_keys = self.schema.get("properties", {}).keys()

        cleaned_dict = {key: value for key, value in record.items() if key in allowed_keys}

        return cleaned_dict

    def receive_record(self):
        """This method is used to receive a post request
        validate the json schema and convert to pandas dataframe

        Args:

        Returns:
            pandas.DataFrame

        """
        record = request.get_json()

        record = self.clean_json(record)

        if not self.validate_json_schema(record):
            return None

        for key, value in record.items():
            if value == "":
                record[key] = None

        df = pd.DataFrame(record, index=[0])

        return df
