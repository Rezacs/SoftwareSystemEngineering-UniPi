import json
import threading
from datetime import datetime, timezone
from pathlib import Path

_log_lock = threading.Lock()

class LoggingManager:

    def __init__(self):
        self._project_root = Path(__file__).resolve().parent
        self._log_path     = self._project_root.parents[2] / "logs" / "evaluationLog.json"
        self._session_key  = None
        self._current_process = None
        self._init_log()

    def _utc_now(self):
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

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
            except (json.JSONDecodeError, ValueError):
                with self._log_path.open("w", encoding="utf-8") as f:
                    json.dump({}, f, indent=4)

    def _read(self):
        try:
            with self._log_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return {}

    def _write(self, data):
        with self._log_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    # =========================================================
    # ================= SESSION ===============================
    # =========================================================

    def start_session(self):
        self._session_key = f"TEMP_{self._utc_now()}"
        with _log_lock:
            data = self._read()
            data[self._session_key] = [
                {
                    "beginning_ts": self._utc_now()
                }
            ]
            self._write(data)

    # =========================================================
    # ================= PROCESS LOGGING =======================
    # =========================================================

    def start_process(self, process_name):
        self._current_process = {
            "process": process_name,
            "initial_ts": self._utc_now()
        }

    def end_process(self, outcome):
        if not self._current_process:
            return  # safety guard

        self._current_process["final_ts"] = self._utc_now()
        self._current_process["outcome"] = outcome

        with _log_lock:
            data = self._read()

            if self._session_key not in data:
                data[self._session_key] = []

            data[self._session_key].append(self._current_process)
            self._write(data)

        self._current_process = None  # reset

    # =========================================================
    # ================= FINALIZE ==============================
    # =========================================================

    def finalize_log(self):
        with _log_lock:
            data = self._read()
            session_data = data.pop(self._session_key, [])

            # move to final timestamp key
            data[self._utc_now()] = session_data

            self._write(data)