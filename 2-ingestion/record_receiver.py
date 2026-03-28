from .utils.json_io import JsonIO


class RecordReceiver:
    def receive_record(self, path: str):
        return JsonIO.load(path)

    def validate_record(self, record: dict) -> bool:
        required_keys = {"player_id", "football", "medical", "social"}
        return required_keys.issubset(record.keys())
