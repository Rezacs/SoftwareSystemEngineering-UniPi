from flask import Flask, request, jsonify

"""
Class which should wait to receive the raw session
"""


class RawSessionReceiver:

    raw_session_required_keys = {"UUID", "created_at", "records"}
    records_required_keys = {"UUID", "player_id","days_missed", "games_missed","number_of_likes", "number_of_followers","skill_overall","label"}


    def validate_json_schema(self, raw_session: dict) -> bool:
        # 1. Validate the top-level session keys first
        if not self.raw_session_required_keys.issubset(raw_session.keys()):
            print("RAW_SESSION_RECEIVER: Invalid raw session attributes")
            return False

        # 2. Safely grab the records (using .get() prevents a KeyError if the key is missing)
        records = raw_session.get("records", [])
        
        # Optional but recommended: ensure 'records' is actually a list
        if not isinstance(records, list):
            print("RAW_SESSION_RECEIVER : records not a list")
            return False

        # 3. Validate each individual record
        for record in records:
            if not self.records_required_keys.issubset(record.keys()):
                print("RAW_SESSION_RECEIVER : record not valid")
                return False
        
        # 4. If the code survives all the checks above, the session is perfectly valid!
        return True
    
    def receive_raw_session(self):
        """
        receive a post request validate the json schema and convert to pandas dataframe
        """
        raw_session = request.get_json()

        if not self.validate_json_schema(raw_session):
            
            return None
        
        return raw_session
        

        
        
    

    
