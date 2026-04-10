import json
from datetime import datetime, timezone
from pathlib import Path


class LoggingManager:

    def __init__(self):

        self._project_root = Path(__file__).resolve().parent

        self._log_path = self._project_root.parents[2] / "logs" / "evaluationLog.json"

        self._session_key = None

        self._init_log()

    def _utc_now(self):

        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _init_log(self):

        self._log_path.parent.mkdir(parents=True, exist_ok=True)

        if not self._log_path.is_file():

            with self._log_path.open("w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)

            return

        # FIX corrupted/empty existing file
        try:
            with self._log_path.open("r", encoding="utf-8") as f:
                json.load(f)

        except (json.JSONDecodeError, ValueError):

            with self._log_path.open("w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)

    def start_session(self):

        self._session_key = f"TEMP_{self._utc_now()}"

        with self._log_path.open("r+", encoding="utf-8") as f:

            data = json.load(f)

            data[self._session_key] = []

            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

    def log_decision(self, decision):

        with self._log_path.open("r+", encoding="utf-8") as f:

            data = json.load(f)

            event = {
                "timestamp": self._utc_now(),
                "process": "Classifier Evaluation",
                "decision": decision
            }

            data[self._session_key].append(event)

            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

    def finalize_log(self, output_type):

        with self._log_path.open("r+", encoding="utf-8") as f:

            data = json.load(f)

            session_data = data.pop(self._session_key)

            session_data.append({
                "output": output_type
            })

            final_timestamp = self._utc_now()

            data[final_timestamp] = session_data

            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()