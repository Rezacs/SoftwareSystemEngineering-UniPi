import numpy as np
import pandas as pd


class PreparedSessionCreator:
    """Transforms raw data sessions into clean, feature-extracted prepared sessions.

    This class provides a pipeline of static methods to process raw session data.
    It handles converting data structures, imputing missing values, clipping absolute
    outliers, and calculating the final composite features needed for downstream
    machine learning or evaluation tasks.
    """

    def __init__(self):
        """Initializes the PreparedSessionCreator."""
        pass

    @staticmethod
    def parse_raw_session(raw_session: dict) -> dict:
        """Converts the session's raw records into a pandas DataFrame for processing.

        This method replaces any Python `None` values with `np.nan` so they can
        be properly handled by pandas mathematical functions in later steps.

        Args:
            raw_session (dict): The initial raw session dictionary containing
                a 'records' key with a list of dictionaries.

        Returns:
            dict: The updated session where the 'records' value is now a pandas DataFrame.
        """
        df = pd.DataFrame(raw_session.get("records", []))

        df = df.replace([None], np.nan)

        raw_session["records"] = df

        return raw_session

    @staticmethod
    def correct_missing_samples(raw_session: dict) -> dict | None:
        """Imputes missing data values and removes records with missing target labels.

        Missing features are filled using median or mean imputation depending
        on the specific field. If a record lacks a 'label', it is considered
        useless for training/evaluation and is dropped entirely.

        Args:
            raw_session (dict): The session dictionary with 'records' as a DataFrame.

        Returns:
            dict | None: The session dictionary with missing values filled.
                Returns None if all records are dropped due to missing labels.
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
            print("[Warning] Raw sessions with missing labels discarded")
            records_df = records_df.dropna(subset=['label'])

            if len(records_df) == 0:
                return None

        # Fill all missing values
        records_df = records_df.fillna(value=replacement_values)

        raw_session["records"] = records_df

        return raw_session

    @staticmethod
    def correct_absolute_outliers(raw_session: dict) -> dict:
        """Clips extreme outliers in the data to predefined acceptable thresholds.

        Args:
            raw_session (dict): The session dictionary with 'records' as a DataFrame.

        Returns:
            dict: The session dictionary with all record values bounded within
                their expected logical limits.
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
        """Calculates composite features and finalizes the prepared session structure.

        This method takes the cleaned raw records and computes new metrics, such
        as the 'social_influence_score' and 'injuries_impact_score'. It then drops
        the old 'records' DataFrame and outputs a finalized dictionary ready for transmission.

        Args:
            raw_session (dict): The cleaned session dictionary with 'records' as a DataFrame.

        Returns:
            dict: The final prepared session containing the 'UUID', 'created_at',
                and the newly computed 'features' as a list of dictionaries.
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
