import numpy as np
import pandas as pd


class PreparedSessionCreator:
    """ """

    def __init__(self):
        pass

    @staticmethod
    def parse_raw_session(raw_session: dict) -> dict:
        """

        Args:
          raw_session: dict: 

        Returns:

        """

        df = pd.DataFrame(raw_session.get("records", []))

        df = df.replace([None], np.nan)

        raw_session["records"] = df

        return raw_session

    @staticmethod
    def correct_missing_samples(raw_session: dict) -> dict:
        """

        Args:
          raw_session: dict: 

        Returns:

        """
        # insert a filling logic for each type of data
        records_df = raw_session.get("records")

        replacement_values = {
            'days_missed': records_df['days_missed'].mean(),
            'games_missed': records_df['games_missed'].mean(),
            'number_of_likes': records_df['number_of_likes'].median(),
            'number_of_followers': records_df['number_of_followers'].median(),
            'skill_overall': records_df['skill_overall'].mean()
        }

        # Check missing labels
        if records_df['label'].isna().sum() > 0:
            print(f"[Warning] Raw sessions with missing labels discarded")
            records_df = records_df.dropna(subset=['label'])

            if len(records_df) == 0:
                return None

        # Fill all missing values
        records_df = records_df.fillna(value=replacement_values)

        raw_session["records"] = records_df

        return raw_session

    @staticmethod
    def correct_absolute_outliers(raw_session: dict) -> dict:
        """

        Args:
          raw_session: dict: 

        Returns:

        """
        # insert a correction logic for each type of outliers

        records_df = raw_session.get("records")

        treshold_values = {
            'days_missed': [0, 365],
            'games_missed': [0, 250],
            'number_of_likes': [0, 100000],
            'number_of_followers': [0, 100000],
            'skill_overall': [60, 99]
        }

        records_df['days_missed'] = records_df['days_missed'].clip(lower=treshold_values["days_missed"][0],
                                                                   upper=treshold_values["days_missed"][1])

        records_df['games_missed'] = records_df['games_missed'].clip(lower=treshold_values["games_missed"][0],
                                                                     upper=treshold_values["games_missed"][1])

        records_df['number_of_likes'] = records_df['number_of_likes'].clip(lower=treshold_values["number_of_likes"][0],
                                                                           upper=treshold_values["number_of_likes"][1])

        records_df['number_of_followers'] = records_df['number_of_followers'].clip(
            lower=treshold_values["number_of_followers"][0], upper=treshold_values["number_of_followers"][1])

        records_df['skill_overall'] = records_df['skill_overall'].clip(lower=treshold_values["skill_overall"][0],
                                                                       upper=treshold_values["skill_overall"][1])

        raw_session["records"] = records_df

        return raw_session

    @staticmethod
    def extract_features(raw_session: dict) -> dict:
        """

        Args:
          raw_session: dict: 

        Returns:

        """

        records_df = raw_session.get("records")

        prepared_session = {"UUID": raw_session["UUID"], "created_at": raw_session["created_at"]}

        features_df = pd.DataFrame()

        features_df["player_id"] = records_df["player_id"]
        features_df["skill_overall"] = records_df["skill_overall"]
        features_df["social_influence_score"] = (0.7 * records_df["number_of_followers"]) + (
                    0.3 * records_df["number_of_likes"])
        features_df["injuries_impact_score"] = (0.7 * records_df["games_missed"]) + (0.3 * records_df["days_missed"])

        features_df["label"] = records_df["label"]

        prepared_session["features"] = features_df.to_dict(orient="records")

        return prepared_session
