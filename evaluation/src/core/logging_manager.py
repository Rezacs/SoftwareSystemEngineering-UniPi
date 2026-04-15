import json
import threading
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

_log_lock = threading.Lock()


class LoggingManager:

    def __init__(self):
        self._project_root = Path(__file__).resolve().parent
        self._log_path = self._project_root.parents[2] / "logs" / "evaluationLog.json"
        self._session_key = None
        self._current_process = None
        self._session_start_ts = None 
        self._init_log()

    def _utc_now(self):
        #return datetime.now(timezone.cet)
        return datetime.now(ZoneInfo("Europe/Rome"))

    def _format_ts(self, dt):
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _init_log(self):
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

        if not self._log_path.is_file():
            with self._log_path.open("w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)
            return

        with _log_lock:
            try:
                with self._log_path.open("r", encoding="utf-8") as f:
                    json.load(f)
            except:
                with self._log_path.open("w", encoding="utf-8") as f:
                    json.dump({}, f, indent=4)

    def _read(self):
        try:
            with self._log_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def _write(self, data):
        with self._log_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    # =========================================================
    # ================= SESSION ===============================
    # =========================================================

    def start_session(self):
        self._session_start_ts = self._utc_now()
        self._session_key = f"TEMP_{self._format_ts(self._session_start_ts)}"

        with _log_lock:
            data = self._read()
            data[self._session_key] = []
            self._write(data)

    # =========================================================
    # ================= PROCESS ===============================
    # =========================================================

    def start_process(self, process_name):
        self._current_process = {
            "process": process_name,
            "start_time": self._utc_now()
        }

    def end_process(self, outcome):
        if not self._current_process:
            return

        end_time = self._utc_now()
        start_time = self._current_process["start_time"]

        latency = (end_time - start_time).total_seconds()

        process_entry = {
            "process": self._current_process["process"],
            "latency": f"{latency:.4f}",
            "outcome": outcome
        }

        with _log_lock:
            data = self._read()

            if self._session_key not in data:
                data[self._session_key] = []

            data[self._session_key].append(process_entry)
            self._write(data)

        self._current_process = None

    # =========================================================
    # ================= FINALIZE ==============================
    # =========================================================

    def finalize_log(self):
        with _log_lock:
            data = self._read()

            session_data = data.pop(self._session_key, [])

            # KEY = SESSION START TIME
            final_key = self._format_ts(self._session_start_ts)

            data[final_key] = session_data

            self._write(data)