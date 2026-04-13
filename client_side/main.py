import json
import time
import random
import threading
import math
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from flask import Flask, request, jsonify

# ── Suppress Flask request logs ───────────────────────────────
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__)

##########################################
# PATHS & CONFIG
##########################################

REPO_ROOT   = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "clientsideConfig.json"
LOG_DIR     = REPO_ROOT / "logs"

def load_config():
    with CONFIG_PATH.open('r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()

LABELS_CSV_PATH = LOG_DIR / "labels.csv"

##########################################
# THREAD PRIMITIVES
##########################################

results_lock   = threading.Lock()
results_storage = {}

log_lock       = threading.Lock()
csv_lock       = threading.Lock()

streaming_done = threading.Event()
streaming_done.set()   # idle at startup

##########################################
# LOGGING HELPERS
##########################################

def log_event(filename, event_data):
    """Append an event dict to a JSON-array log file."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / filename
    with log_lock:
        logs = []
        if path.exists():
            with path.open('r', encoding='utf-8') as f:
                try:
                    logs = json.load(f)
                except Exception:
                    logs = []
        logs.append(event_data)
        with path.open('w', encoding='utf-8') as f:
            json.dump(logs, indent=4, fp=f)


def clear_logs():
    """Wipe all system log files at the start of each experiment."""
    log_files = [
        "clientsideLogs.json",
        "ingestionLog.json",
        "preparationLog.json",
        "segregationLog.json",
        "developmentLog.json",
        "productionLog.json",
        "evaluationLog.json",
    ]
    with log_lock:
        for name in log_files:
            path = LOG_DIR / name
            if path.exists():
                empty = "[]" if name == "clientsideLogs.json" else "{}"
                path.write_text(empty, encoding="utf-8")

##########################################
# CSV HELPERS
##########################################

def _read_csv_safe(path):
    """Read a CSV, returning an empty DataFrame on any parse failure."""
    try:
        df = pd.read_csv(path)
        if df.empty or len(df.columns) == 0:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()


def _append_to_csv(path, new_df):
    """Thread-safe append of new_df rows to a CSV file."""
    with csv_lock:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.stat().st_size > 0:
            existing = _read_csv_safe(path)
            combined = pd.concat([existing, new_df], ignore_index=True) \
                       if not existing.empty else new_df
        else:
            combined = new_df
        combined.to_csv(path, index=False)

##########################################
# TEST LOG GENERATOR
##########################################

def parse_ts(ts_str):
    """Normalize timestamps to naive UTC datetimes for safe arithmetic."""
    if ts_str is None:
        return None
    ts_str = ts_str.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(ts_str)
        return dt.replace(tzinfo=None)
    except ValueError:
        return None


def generate_testing_csv(current_phase):
    phase_label = "Development" if current_phase == "0" else "Production"
    print(f"\n[SYSTEM] Aggregating logs for {phase_label} phase...")

    all_logs = ["ingestionLog.json", "preparationLog.json"]
    if current_phase == "0":
        all_logs += ["segregationLog.json", "developmentLog.json", "productionLog.json"]
    else:
        all_logs += ["productionLog.json", "evaluationLog.json"]
    all_logs = list(dict.fromkeys(all_logs))   # deduplicate, preserve order

    rows = []

    for log_file in all_logs:
        path        = LOG_DIR / log_file
        system_name = log_file.replace("Log.json", "")

        if not path.exists():
            continue

        with log_lock:
            with path.open('r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except Exception as e:
                    print(f"  Error reading {log_file}: {e}")
                    continue

        if not isinstance(data, dict):
            continue

        for _session_ts, entries in data.items():
            for entry in entries:
                rows.append({
                    "system":    system_name,
                    "process":   entry.get("process"),
                    "latency_s": entry.get("latency", 0),
                    "outcome":   entry.get("outcome", ""),
                })

    if not rows:
        print("  FAILED: No process entries found in logs.")
        return

    phase_name  = "development" if current_phase == "0" else "production"
    output_path = LOG_DIR / f"testing_log_{phase_name}.csv"
    _append_to_csv(output_path, pd.DataFrame(rows))
    print(f"  SUCCESS: {len(rows)} rows written → {output_path}")

##########################################
# STREAMING WORKER
##########################################

def stream_worker(current_phase, limit, record_list):
    streaming_done.clear()

    ingestion_cfg   = config['network']['ingestion_system']
    url             = f"http://{ingestion_cfg['ip']}:{ingestion_cfg['port']}/run"
    total_available = len(record_list)

    consecutive_failures = 0
    MAX_BACKOFF_S        = 10.0

    for i in range(limit):
        # reshuffle each full cycle
        if i > 0 and i % total_available == 0:
            random.shuffle(record_list)

        record = record_list[i % total_available]
        p_id   = record.get('player_id')
        if p_id is not None:
            p_id = int(p_id)

        try:
            response = requests.post(url, json=record, timeout=5)
            print(f"  Sent [{i+1}/{limit}] player {p_id} → {response.status_code}")
            consecutive_failures = 0

        except Exception:
            consecutive_failures += 1
            backoff = min(0.5 * (2 ** (consecutive_failures - 1)), MAX_BACKOFF_S)
            print(f"  Target {url} unreachable. "
                  f"(failure #{consecutive_failures}, retrying in {backoff:.1f}s)")
            time.sleep(backoff)

    print("\n[SYSTEM] Streaming finished.")
    streaming_done.set()

##########################################
# FLASK ROUTES
##########################################

@app.route("/receive-label", methods=["POST"])
def receive_label():
    try:
        data = request.get_json()
        p_id = data.get("player_id")
        if p_id is not None:
            p_id = int(p_id)

        with results_lock:
            results_storage[p_id] = data

        new_row = {
            "player_id": int(p_id) if p_id is not None else None,
            "timestamp": datetime.now().isoformat(),
            **{k: v for k, v in data.items() if k != "player_id"},
        }
        _append_to_csv(LABELS_CSV_PATH, pd.DataFrame([new_row]))

        return jsonify({"status": "received"}), 200

    except Exception as e:
        print(f"[CLIENT] Error in /receive-label: {e}")
        return jsonify({"error": str(e)}), 500


def run_flask():
    app.run(
        host=config['network']['listen_host'],
        port=config['network']['listen_port'],
        use_reloader=False,
    )

##########################################
# DATA LOADER
##########################################

def load_record_list():
    """Load and interleave all dev CSVs into a shuffled flat record list."""
    pool = []
    for file_path in config['paths']['dev_files']:
        candidate = Path(file_path)
        if not candidate.is_absolute():
            candidate = (REPO_ROOT / candidate).resolve()

        if candidate.exists():
            df = pd.read_csv(candidate)
            df = df.where(pd.notnull(df), None).sample(frac=1).reset_index(drop=True)
            pool.append(df)
        else:
            print(f"  Warning: {candidate} not found, skipping.")

    records = []
    for df in pool:
        for _, row in df.iterrows():
            records.append({
                k: v for k, v in row.to_dict().items()
                if v is not None and not (isinstance(v, float) and math.isnan(v))
            })

    random.shuffle(records)
    return records

##########################################
# MAIN CONTROL LOOP
##########################################

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()

    while True:
        # ── Reset logs for this experiment ────────────────────
        clear_logs()
        log_event("clientsideLogs.json", {
            "initial_experiment_timestamp": datetime.now().isoformat()
        })

        print("\n" + "=" * 40)
        print("CLIENT SYSTEM CONTROL PANEL")
        print("=" * 40)

        phase_choice = input("Select Phase: [0] Development, [1] Production: ").strip()
        stream_limit = int(input("Enter number of records to stream: ").strip())

        record_list = load_record_list()
        if not record_list:
            print("  ERROR: No records loaded. Check config paths.")
            continue

        # ── Start background stream ────────────────────────────
        threading.Thread(
            target=stream_worker,
            args=(phase_choice, stream_limit, record_list),
            daemon=True,
        ).start()

        print("Waiting for streaming to complete...")
        streaming_done.wait()

        print("Waiting for last labels to arrive...")
        time.sleep(3)

        print("\n" + "=" * 40)
        if input("Ready to generate testing log CSV? (y/n): ").strip().lower() == 'y':
            generate_testing_csv(phase_choice)
        else:
            print("  Skipping CSV generation.")

        print("\nRestarting system...")