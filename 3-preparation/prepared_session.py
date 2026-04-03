import pandas as pd

class prepared_session:

    def __init__(self,raw_session : dict):
        
        self.uuid=raw_session.get("uuid",-1)
        self.created_at=raw_session.get("created_at","99/99/9999")
        self.records=pd.DataFrame(raw_session.get("records",[]))

    def get_uuid(self):

        return self.uuid
    
    def get_records_dataframe(self):
        
        return self.records
    
    def set_records_dataframe(self,records : pd.DataFrame):

        self.records=records