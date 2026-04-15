import json
from pathlib import Path

from flask import request
from jsonschema import validate, ValidationError


class RawSessionReceiver:
    """Waits to receive a raw session and validates its structure.

    This class handles the reception of incoming raw session payloads via HTTP
    requests and ensures they strictly adhere to a predefined JSON schema before
    they are allowed to proceed further into the system.

    Attributes:
        schema (dict): The loaded JSON schema used for validation.
    """

    def __init__(self, schema_path: str):
        """Initializes the receiver and loads the JSON validation schema.

        Args:
            schema_path (str): The relative path to the JSON schema file.

        Raises:
            FileNotFoundError: If the schema file cannot be located at the resolved path.
            json.JSONDecodeError: If the schema file contains invalid JSON.
        """
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
        """Validates a raw session dictionary against the loaded JSON schema.

        Args:
            raw_session (dict): The parsed JSON payload to validate.

        Returns:
            bool: True if the session matches the schema perfectly, False if a
                validation error occurs.
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
        """Extracts and validates a JSON payload from an active HTTP POST request.

        This method must be called within an active Flask request context. It attempts
        to parse the JSON body of the incoming request and runs it through the schema
        validator.

        Returns:
            dict or None: Returns the validated raw session dictionary if successful,
                or None if the payload fails validation.
        """
        raw_session = request.get_json()

        if not self.validate_json_schema(raw_session):
            return None

        return raw_session
