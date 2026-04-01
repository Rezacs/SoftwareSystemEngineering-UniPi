"""Validates the prepared-session JSON received by the Segregation System before storage."""

from .json_io import JsonIO


class SchemaValidator:
    def __init__(self, schema_path: str):
        self.schema_path = schema_path

    def validatePreparedSession(self, payload: dict) -> tuple[bool, str]:
        if not isinstance(payload, dict):
            return False, "Payload must be a JSON object"

        try:
            schema = JsonIO.load(self.schema_path)
        except FileNotFoundError:
            schema = {}

        required_keys = schema.get("required") or [
            "session_id",
            "player_id",
            "skill_overall",
            "social_influence_score",
            "injuries_impact_score",
        ]
        for key in required_keys:
            if key not in payload:
                return False, f"Missing required field: {key}"

        required_numeric_keys = [
            "skill_overall",
            "social_influence_score",
            "injuries_impact_score",
        ]
        for key in required_numeric_keys:
            value = payload.get(key)
            if not isinstance(value, (int, float)):
                return False, f"Field '{key}' must be a number"

        return True, "ok"
