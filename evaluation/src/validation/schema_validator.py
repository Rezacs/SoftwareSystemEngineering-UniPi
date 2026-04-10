import json
from pathlib import Path
from jsonschema import validate, ValidationError


class SchemaValidator:

    def __init__(self):

        base_dir = Path(__file__).resolve().parents[2]
        path = base_dir / "data" / "schema" / "label_schema.json"

        if not path.exists():
            raise FileNotFoundError(f"Schema not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            self.schema = json.load(f)

    def validate(self, data):
        try:
            validate(instance=data, schema=self.schema)
        except ValidationError as e:
            raise ValueError(f"Invalid input schema → {e.message}")