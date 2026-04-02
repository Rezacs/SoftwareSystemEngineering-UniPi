import random
from dataclasses import asdict

from common.csv_reader import CSVReader
from common.data_merger import DataMerger
from common.json_io import JsonIO


class ClientSideService:
    def __init__(self):
        self.reader = CSVReader()
        self.merger = DataMerger()

    def load_merged_records(self):
        football_records = self.reader.read_football_data("data/inputs/raws_football_db.csv")
        medical_records = self.reader.read_medical_data("data/inputs/raws_medical_db.csv")
        social_records = self.reader.read_social_data("data/inputs/raws_social_db.csv")

        return self.merger.merge_by_player_id(
            football_records,
            medical_records,
            social_records
        )

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