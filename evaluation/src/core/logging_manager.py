import os
import json
from datetime import datetime, timezone


class LoggingManager:

    def __init__(self):

        self._project_root = os.path.dirname(os.path.abspath(__file__))

        self._log_path = os.path.abspath(
            os.path.join(
                self._project_root,
                "..",
                "..",
                "..",
                "log",
                "evaluationLog.json"
            )
        )

        self._session_key = None

        self._init_log()

    def _utc_now(self):

        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _init_log(self):

        os.makedirs(os.path.dirname(self._log_path), exist_ok=True)

        if not os.path.isfile(self._log_path):

            with open(self._log_path, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)

    def start_session(self):

        self._session_key = f"TEMP_{self._utc_now()}"

        with open(self._log_path, "r+", encoding="utf-8") as f:

            data = json.load(f)

            data[self._session_key] = []

            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

    def log_decision(self, decision):

        with open(self._log_path, "r+", encoding="utf-8") as f:

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

        with open(self._log_path, "r+", encoding="utf-8") as f:

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