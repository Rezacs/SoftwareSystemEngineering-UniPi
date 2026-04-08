from datetime import datetime
import pandas as pd
import uuid


class RawSessionCreator:

    def __init__(self,sufficient_record_treshold : int = 1):
        
        self.sufficient_record_treshold=sufficient_record_treshold


    def isNumberOfRecordsSufficient(self,available_records_num) -> bool:

        return available_records_num>=self.sufficient_record_treshold

    @staticmethod
    def create_raw_session(dataframe : pd.DataFrame) -> dict:
        
        session_uuid=str(uuid.uuid4())
        
        dataframe['UUID']=session_uuid

        return {
            "UUID": f"{session_uuid}",
            "created_at": datetime.now().isoformat(),
            "records": dataframe.to_dict(orient="records")
        }
    
    @staticmethod
    def mark_missing_samples(raw_session : dict) -> float:

        dataframe=pd.DataFrame(raw_session['records'])

        number_of_samples=len(dataframe)

        number_of_missing_values=dataframe.isna().sum().sum()

        return number_of_missing_values/number_of_samples if number_of_samples > 0 else 0.0
        
       