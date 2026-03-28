import json
from pathlib import Path


class JsonIO:
    @staticmethod
    def load(path: str):
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def save(path: str, data):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

