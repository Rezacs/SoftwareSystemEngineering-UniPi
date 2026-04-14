import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

_log_lock = threading.Lock()


class LoggingManager:

    def __init__(self):
        self._project_root = Path(__file__).resolve().parent
        self._log_path = self._project_root.parents[2] / "logs" / "evaluationLog.json"
        self._sessions = {}
        self._sessions_lock = threading.Lock()
        self._init_log()

    def _utc_now(self):
        return datetime.now(timezone.utc)

    def _format_ts(self, dt):
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")

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
            json.dump(data, f, indent=4, sort_keys=True)

    def _build_unique_final_key(self, data, base_key):
        if base_key not in data:
            return base_key

        suffix = 1
        while True:
            candidate = f"{base_key}__{suffix}"
            if candidate not in data:
                return candidate
            suffix += 1

    # =========================================================
    # ================= SESSION ===============================
    # =========================================================

    def start_session(self):
        session_start_ts = self._utc_now()
        session_key = f"TEMP_{self._format_ts(session_start_ts)}_{uuid4().hex[:8]}"

        with self._sessions_lock:
            self._sessions[session_key] = {
                "session_start_ts": session_start_ts,
                "current_process": None,
            }

        with _log_lock:
            data = self._read()
            data[session_key] = []
            self._write(data)

        return session_key

    # =========================================================
    # ================= PROCESS ===============================
    # =========================================================

    def start_process(self, session_key, process_name):
        with self._sessions_lock:
            session = self._sessions.get(session_key)
            if session is None:
                return

            session["current_process"] = {
            "process": process_name,
            "start_time": self._utc_now()
            }

    def end_process(self, session_key, outcome):
        with self._sessions_lock:
            session = self._sessions.get(session_key)
            if session is None or not session.get("current_process"):
                return

            current_process = session["current_process"]

        if not current_process:
            return

        end_time = self._utc_now()
        start_time = current_process["start_time"]

        latency_ms = (end_time - start_time).total_seconds() * 1000
        latency = latency_ms / 1000

        process_entry = {
            "process": current_process["process"],
            "latency": f"{latency:.4f}",
            "outcome": outcome
        }

        with _log_lock:
            data = self._read()

            if session_key not in data:
                data[session_key] = []

            data[session_key].append(process_entry)
            self._write(data)

        with self._sessions_lock:
            session = self._sessions.get(session_key)
            if session is not None:
                session["current_process"] = None

    # =========================================================
    # ================= FINALIZE ==============================
    # =========================================================

    def finalize_log(self, session_key):
        with self._sessions_lock:
            session = self._sessions.get(session_key)
            if session is None:
                return

            session_start_ts = session["session_start_ts"]

        with _log_lock:
            data = self._read()

            session_data = data.pop(session_key, [])

            # KEY = SESSION START TIME
            final_key = self._build_unique_final_key(data, self._format_ts(session_start_ts))

            data[final_key] = session_data

            self._write(data)

        with self._sessions_lock:
            self._sessions.pop(session_key, None)