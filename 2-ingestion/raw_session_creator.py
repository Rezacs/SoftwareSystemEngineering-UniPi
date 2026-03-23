from datetime import datetime


class RawSessionCreator:
    def create_raw_session(self, record: dict) -> dict:
        return {
            "session_id": f"raw-session-{record['player_id']}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "created_at": datetime.now().isoformat(),
            "records": [record]
        }