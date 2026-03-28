from .models import CombinedPlayerRecord


class DataMerger:
    def merge_by_player_id(self, football_records, medical_records, social_records):
        football_map = {record.player_id: record for record in football_records}
        medical_map = {record.player_id: record for record in medical_records}
        social_map = {record.player_id: record for record in social_records}

        all_ids = (
            set(football_map.keys())
            | set(medical_map.keys())
            | set(social_map.keys())
        )

        merged_records = []
        for player_id in all_ids:
            merged_records.append(
                CombinedPlayerRecord(
                    player_id=player_id,
                    football=football_map.get(player_id),
                    medical=medical_map.get(player_id),
                    social=social_map.get(player_id),
                )
            )

        return merged_records

