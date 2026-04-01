from datetime import datetime


class TimestampLogController:
    def create_log_entry(self, event_name: str):
        return {
            "event": event_name,
            "timestamp": datetime.now().isoformat()
        }