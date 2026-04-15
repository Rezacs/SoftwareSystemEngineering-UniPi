import sys
import uuid
from datetime import datetime

import numpy as np
import pandas as pd


class RawSessionCreator:
    """Creates and validates raw data sessions from incoming records.

    This class evaluates if there is a sufficient amount of data to process,
    packages DataFrames into structured session dictionaries with unique IDs,
    and analyzes the quality of the session data by checking for missing values.

    Attributes:
        sufficient_record_treshold (int): The minimum number of records required
            to consider a batch sufficient for session creation.
    """

    def __init__(self, sufficient_record_treshold: int = 1):
        """Initializes the RawSessionCreator with a specific record threshold.

        Args:
            sufficient_record_treshold (int, optional): The minimum threshold
                for records. Defaults to 1.
        """
        self.sufficient_record_treshold = sufficient_record_treshold

    def is_number_of_records_sufficient(self, available_records_num) -> bool:
        """Checks if the available records meet the minimum threshold requirement.

        Args:
            available_records_num (int): The current count of available records.

        Returns:
            bool: True if the number of records is greater than or equal to
                the threshold, False otherwise.
        """
        return available_records_num >= self.sufficient_record_treshold

    @staticmethod
    def create_raw_session(dataframe: pd.DataFrame) -> dict:
        """Packages a DataFrame of records into a structured session dictionary.

        This method generates a unique UUID for the session, appends it to all
        records in the DataFrame, replaces any NaN values with None (for JSON
        compatibility), and builds the final session payload.

        Args:
            dataframe (pd.DataFrame): The input data containing the records.

        Returns:
            dict: A dictionary containing the session 'UUID', 'created_at'
                timestamp, and 'records' as a list of dictionaries.
        """
        session_uuid = str(uuid.uuid4())

        dataframe['UUID'] = session_uuid

        dataframe = dataframe.replace(np.nan, None)

        return {
            "UUID": f"{session_uuid}",
            "created_at": datetime.now().isoformat(),
            "records": dataframe.to_dict(orient="records")
        }

    @staticmethod
    def mark_missing_samples(raw_session: dict):
        """Calculates the ratio of missing values in a given raw session.

        This method converts the session records back into a DataFrame to
        count nulls and empty strings. If any target 'label' values are missing,
        it immediately returns the system's max integer size as an error flag.

        Args:
            raw_session (dict): The session dictionary containing 'records'.

        Returns:
            float: The ratio of missing values relative to the number of samples
                (total missing values / total rows). Returns sys.maxsize if
                required labels are missing.
        """


        dataframe = pd.DataFrame(raw_session['records'])


        number_of_samples = len(dataframe)

        # marking

        dataframe = dataframe.replace([None, ""], np.nan)


        number_of_missing_values = dataframe.isna().sum().sum()

        missing_label = dataframe["label"].isna().sum()

        if missing_label > 0:
            return sys.maxsize

        ratio = number_of_missing_values / number_of_samples if number_of_samples > 0 else 0.0

        return ratio
