import json
import os
from jsonschema import validate, ValidationError


class SchemaValidator:

    def __init__(self):

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(base_dir, "data", "schema", "label_schema.json")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Schema not found: {path}")

        with open(path, "r") as f:
            self.schema = json.load(f)

    def validate(self, data):
        try:
            validate(instance=data, schema=self.schema)
        except ValidationError as e:
            raise ValueError(f"Invalid input schema → {e.message}")