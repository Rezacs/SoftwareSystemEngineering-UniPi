import pandas as pd

from .models import FootballRecord, MedicalRecord, SocialRecord


class CSVReader:
    def read_football_data(self, path: str) -> list[FootballRecord]:
        df = pd.read_csv(path)
        records = []

        for _, row in df.iterrows():
            records.append(
                FootballRecord(
                    player_id=int(row["player_id"]),
                    short_name=str(row["short_name"]),
                    long_name=str(row["long_name"]),
                    age=int(row["age"]),
                    height_cm=float(row["height_cm"]),
                    weight_kg=float(row["weight_kg"]),
                    club_name=str(row["club_name"]),
                    league_name=str(row["league_name"]),
                    nationality_name=str(row["nationality_name"]),
                    preferred_foot=str(row["preferred_foot"]),
                    overall=float(row["overall"]),
                    potential=float(row["potential"]),
                    shooting=float(row["shooting"]),
                    passing=float(row["passing"]),
                    dribbling=float(row["dribbling"]),
                    defending=float(row["defending"]),
                    physic=float(row["physic"]),
                )
            )

        return records

    def read_medical_data(self, path: str) -> list[MedicalRecord]:
        df = pd.read_csv(path)
        records = []

        for _, row in df.iterrows():
            records.append(
                MedicalRecord(
                    player_id=int(row["player_id"]),
                    player_name=str(row["player_name"]),
                    position=str(row["position"]),
                    main_position=str(row["main_position"]),
                    current_club_name=str(row["current_club_name"]),
                    days_missed=float(row["days_missed"]),
                    games_missed=float(row["games_missed"]),
                    injury_reason=str(row["injury_reason"]),
                    season_name=str(row["season_name"]),
                )
            )

        return records

    def read_social_data(self, path: str) -> list[SocialRecord]:
        df = pd.read_csv(path)
        records = []

        for _, row in df.iterrows():
            records.append(
                SocialRecord(
                    player_id=int(row["id_player"]),
                    short_name=str(row["short_name"]),
                    number_of_likes=int(row["numberOfLikes"]),
                    number_of_followers=int(row["numberOfFollowers"]),
                )
            )

        return records

