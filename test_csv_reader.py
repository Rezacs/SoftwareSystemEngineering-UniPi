from common.csv_reader import CSVReader

reader = CSVReader()

football_records = reader.read_football_data("data/inputs/raws_football_db.csv")
medical_records = reader.read_medical_data("data/inputs/raws_medical_db.csv")
social_records = reader.read_social_data("data/inputs/raws_social_db.csv")

print("Football:", football_records[0])
print("Medical:", medical_records[0])
print("Social:", social_records[0])