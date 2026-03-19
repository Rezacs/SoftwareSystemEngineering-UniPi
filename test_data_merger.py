from common.csv_reader import CSVReader
from common.data_merger import DataMerger

reader = CSVReader()
merger = DataMerger()

football_records = reader.read_football_data("data/inputs/raws_football_db.csv")
medical_records = reader.read_medical_data("data/inputs/raws_medical_db.csv")
social_records = reader.read_social_data("data/inputs/raws_social_db.csv")

merged_records = merger.merge_by_player_id(
    football_records,
    medical_records,
    social_records
)

print(merged_records[0])