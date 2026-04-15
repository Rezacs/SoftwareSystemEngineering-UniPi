import json
from pathlib import Path

from flask import request
from jsonschema import validate, ValidationError

"""
Class which should wait to receive the raw session
"""


class RawSessionReceiver:
    """ """

    def __init__(self, schema_path: str):

        try:
            schema_path = Path(__file__).resolve().parents[0] / schema_path

            with schema_path.open(encoding="utf-8") as f:
                # load the entire JSON file as our schema
                self.schema = json.load(f)

            print("[INFO] JSON Schema correctly loaded")

        except FileNotFoundError:
            print("ERROR> Raw session receiver : JSON schema file not found")
            raise
        except json.JSONDecodeError:
            print("ERROR> Raw session receiver : Error decoding json file")
            raise

    def validate_json_schema(self, raw_session: dict) -> bool:
        """

        Args:
          raw_session: dict: 

        Returns:

        """

        try:
            # compares the raw session against the loaded schema
            validate(instance=raw_session, schema=self.schema)

            return True

        except ValidationError as e:
            # If it fails, the library tells us exactly why 

            print(f"[INFO] Validation failed: {e.message}")

            return False

    def receive_raw_session(self):
        """receive a post request validate the json schema and convert to pandas dataframe"""
        raw_session = request.get_json()

        if not self.validate_json_schema(raw_session):
            return None

        return raw_session
