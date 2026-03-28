import random
from dataclasses import asdict

from .utils.csv_reader import CSVReader
from .utils.data_merger import DataMerger
from .utils.json_io import JsonIO
from .utils.label_table_builder import LabelTableBuilder


class ClientSideService:
    def __init__(self):
        self.reader = CSVReader()
        self.merger = DataMerger()
        self.label_builder = LabelTableBuilder()

    def load_label_map(self, path="data/inputs/labels_db.json"):
        try:
            label_rows = JsonIO.load(path)
        except FileNotFoundError:
            return {}

        if not isinstance(label_rows, list):
            return {}

        return self.label_builder.build_map(label_rows)

    def load_merged_records(self):
        football_records = self.reader.read_football_data("data/inputs/raws_football_db.csv")
        medical_records = self.reader.read_medical_data("data/inputs/raws_medical_db.csv")
        social_records = self.reader.read_social_data("data/inputs/raws_social_db.csv")
        label_map = self.load_label_map()

        merged_records = self.merger.merge_by_player_id(
            football_records,
            medical_records,
            social_records
        )

        for record in merged_records:
            record.label = label_map.get(record.player_id)

        return merged_records

    def get_random_record(self):
        merged_records = self.load_merged_records()
        return random.choice(merged_records)

    def build_json_message(self):
        record = self.get_random_record()
        return asdict(record)

    def save_json_message(self, output_path="data/outputs/client_message.json"):
        message = self.build_json_message()
        JsonIO.save(output_path, message)
        return message
