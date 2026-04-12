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

    # =========================================================
    # ================= MAIN VALIDATION ========================
    # =========================================================

    def validate(self, data):

        # ================= SCHEMA VALIDATION =================
        try:
            validate(instance=data, schema=self.schema)
        except ValidationError as e:
            raise ValueError(f"Invalid input schema → {e.message}")

        # ================= SEMANTIC VALIDATION =================

        # Label must be integer in range 1–5
        label = data.get("label")
        if label not in [1, 2, 3, 4, 5]:
            raise ValueError("Invalid input → 'label' must be an integer between 1 and 5")

        # player_id must be positive integer
        player_id = data.get("player_id")
        if not isinstance(player_id, int) or player_id < 0:
            raise ValueError("Invalid input → 'player_id' must be a positive integer")

        # source must be valid (extra safety)
        source = data.get("source")
        if source not in ["expert", "classifier"]:
            raise ValueError("Invalid input → 'source' must be 'expert' or 'classifier'")