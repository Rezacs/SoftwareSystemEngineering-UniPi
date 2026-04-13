"""Provides local JSON load/save helpers for the Segregation System."""

import json
import math
from pathlib import Path


class JsonIO:
    @staticmethod
    def _normalize_json_value(value):
        if isinstance(value, dict):
            return {
                key: JsonIO._normalize_json_value(inner_value)
                for key, inner_value in value.items()
            }

        if isinstance(value, list):
            return [JsonIO._normalize_json_value(item) for item in value]

        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"none", "null", "nan", "inf", "-inf", "infinity", "-infinity"}:
                return None
            return value

        if isinstance(value, float) and not math.isfinite(value):
            return None

        return value

    @staticmethod
    def load(path: str):
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return JsonIO._normalize_json_value(data)

    @staticmethod
    def save(path: str, data):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        normalized_data = JsonIO._normalize_json_value(data)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(normalized_data, file, indent=4, allow_nan=False)
