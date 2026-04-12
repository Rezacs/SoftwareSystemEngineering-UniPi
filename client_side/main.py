import json
import time
import random
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
import pandas as pd
import requests
import math
app = Flask(__name__)
# Add at the top with other imports
import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Volatile storage
results_storage = {}
streaming_active = False

##########################################
# CONFIG & INITIAL LOGGING
##########################################

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "clientsideConfig.json"
LOG_DIR = REPO_ROOT / "logs"

def load_config():
    with CONFIG_PATH.open('r', encoding='utf-8') as f:
        return json.load(f)

def log_event(filename, event_data):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / filename
    logs = []
    if path.exists():
        with path.open('r', encoding='utf-8') as f:
            try: logs = json.load(f)
            except: logs = []
    logs.append(event_data)
    with path.open('w', encoding='utf-8') as f:
        json.dump(logs, indent=4, fp=f)

config = load_config()

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
        # Strip timezone info to make all datetimes offset-naive
        return dt.replace(tzinfo=None)
    except ValueError:
        return None


def generate_testing_csv(current_phase):
    print("\n[SYSTEM] Aggregating logs for performance analysis...")

    shared_logs = ["ingestionLog.json", "preparationLog.json"]
    if current_phase == "0":
        phase_logs    = ["segregationLog.json", "developmentLog.json"]
        last_log_file = "developmentLog.json"
    else:
        phase_logs    = ["productionLog.json", "evaluationLog.json"]
        last_log_file = "evaluationLog.json"

    all_logs = shared_logs + phase_logs  # ordered pipeline sequence

    # ── 1. Read initial_experiment_ts ───────────────────────────────────────
    initial_ts_str = None
    clientside_path = LOG_DIR / "clientsideLogs.json"
    if clientside_path.exists():
        with clientside_path.open('r', encoding='utf-8') as f:
            try:
                entries = json.load(f)
                for entry in reversed(entries):
                    if "initial_experiment_timestamp" in entry:
                        initial_ts_str = entry["initial_experiment_timestamp"]
                        break
            except Exception as e:
                print(f"Error reading clientsideLogs.json: {e}")

    if not initial_ts_str:
        print("FAILED: No initial_experiment_timestamp found in clientsideLogs.json.")
        return

    # ── 2. For each system log, extract ALL intermediate + final timestamps ─
    row = {"initial_experiment_ts": initial_ts_str}
    last_system_ts_str = None

    for log_file in all_logs:
        path = LOG_DIR / log_file
        base_name = log_file.replace(".json", "")

        if not path.exists():
            print(f"Warning: {log_file} not found, skipping.")
            row[f"{base_name}_final_ts"] = None
            continue

        with path.open('r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"Error reading {log_file}: {e}")
                row[f"{base_name}_final_ts"] = None
                continue

        if not isinstance(data, dict) or not data:
            print(f"Warning: {log_file} is empty or not a dict.")
            row[f"{base_name}_final_ts"] = None
            continue

        # Last outer key = final output timestamp for this system
        last_outer_key = list(data.keys())[-1]
        entries        = data[last_outer_key]

        # Walk the inner process entries — each with a timestamp + process name
        process_idx = 0
        # Walk the inner process entries — each with a timestamp + process name
        for entry in entries:
            if "timestamp" in entry and "process" in entry:
                process_name = entry["process"].strip().replace(" ", "_").lower()
                row[f"{base_name}_{process_name}_ts"] = entry["timestamp"]

        # Final output timestamp (outer key)
        row[f"{base_name}_final_ts"] = last_outer_key

        if log_file == last_log_file:
            last_system_ts_str = last_outer_key

    # ── 3. Compute total experiment duration ────────────────────────────────
    initial_dt     = parse_ts(initial_ts_str)
    last_system_dt = parse_ts(last_system_ts_str)

    if initial_dt and last_system_dt:
        row["experiment_duration_s"] = round(
            (last_system_dt - initial_dt).total_seconds(), 3
        )
    else:
        row["experiment_duration_s"] = None
        print("Warning: Could not compute experiment duration.")

    # ── 4. Append row to CSV ────────────────────────────────────────────────
    phase_name  = "development" if current_phase == "0" else "production"
    output_path = LOG_DIR / f"testing_log_{phase_name}.csv"

    new_df = pd.DataFrame([row])

    if output_path.exists():
        existing_df = pd.read_csv(output_path)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined_df = new_df

    combined_df.to_csv(output_path, index=False)
    print(f"SUCCESS: Row appended → {output_path}")
    print(f"         Experiment duration: {row.get('experiment_duration_s')}s")

##########################################
# STREAMING WORKER
##########################################

def stream_worker(current_phase, limit, record_list):
    global streaming_active
    streaming_active = True

    ingestion_cfg = config['network']['ingestion_system']
    url = f"http://{ingestion_cfg['ip']}:{ingestion_cfg['port']}/run"
    total_available = len(record_list)

    for i in range(limit):
        record = record_list[i % total_available]
        p_id = record.get('player_id')
        if p_id is not None:
            p_id = int(p_id)

        try:
            response = requests.post(url, json=record, timeout=5)
            print(f"  Sent [{i+1}/{limit}] player {p_id} → {response.status_code}")
        except:
            print(f"  Target {url} unreachable.")

    print("\n[SYSTEM] Streaming finished.")
    streaming_active = False

##########################################
# FLASK INTERFACE
##########################################

LABELS_CSV_PATH = LOG_DIR / "labels.csv"

@app.route("/receive-label", methods=["POST"])
def receive_label():
    try:
        data = request.get_json()
        p_id = data.get("player_id")
        if p_id is not None:
            p_id = int(p_id)
        results_storage[p_id] = data

        new_row = {
            "player_id": int(p_id) if p_id is not None else None,
            "timestamp": datetime.now().isoformat(),
            **{k: v for k, v in data.items() if k != "player_id"}
        }
        new_df = pd.DataFrame([new_row])

        if LABELS_CSV_PATH.exists() and LABELS_CSV_PATH.stat().st_size > 0:
            existing_df = pd.read_csv(LABELS_CSV_PATH)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            combined_df = new_df

        combined_df.to_csv(LABELS_CSV_PATH, index=False)
        return jsonify({"status": "received"}), 200

    except Exception as e:
        print(f"[CLIENT] Error in /receive-label: {e}")
        return jsonify({"error": str(e)}), 500

def run_flask():
    app.run(host=config['network']['listen_host'], 
            port=config['network']['listen_port'], 
            use_reloader=False)

##########################################
# MAIN CONTROL LOOP
##########################################

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    log_event("clientsideLogs.json", {
        "initial_experiment_timestamp": datetime.now().isoformat()
    })

    while True:
    # ── Clear all logs at the start of each experiment ──
        for log_file in [
            "clientsideLogs.json",
            "ingestionLog.json",
            "preparationLog.json",
            "segregationLog.json",
            "developmentLog.json",
            "productionLog.json",
            "evaluationLog.json"
        ]:
            path = LOG_DIR / log_file
            if path.exists():
                path.write_text("{}" if log_file != "clientsideLogs.json" else "[]", encoding="utf-8")

        # Write initial timestamp fresh
        log_event("clientsideLogs.json", {
            "initial_experiment_timestamp": datetime.now().isoformat()
        })

        print("\n" + "="*40)
        print("CLIENT SYSTEM CONTROL PANEL")
        print("="*40)
        
        phase_choice = input("Select Phase: [0] Development, [1] Production: ")
        stream_limit = int(input("Enter number of records to stream: "))

        # Prepare Data
        # Prepare Data — same logic for both phases, always load all dev_files
        pool_list = []
        for file_path in config['paths']['dev_files']:
            candidate_path = Path(file_path)
            if not candidate_path.is_absolute():
                candidate_path = (REPO_ROOT / candidate_path).resolve()
                if candidate_path.exists():
                    df = pd.read_csv(candidate_path)
                    df = df.where(pd.notnull(df), None).sample(frac=1).reset_index(drop=True)
                    pool_list.append(df)
            else:
                print(f"Warning: {candidate_path} not found, skipping.")

        # Build flat interleaved list, each record with only its own columns
        record_list = []
        for df in pool_list:
            for _, row in df.iterrows():
                record_list.append({
                k: v for k, v in row.to_dict().items()
                if v is not None and not (isinstance(v, float) and math.isnan(v))
            })
        random.shuffle(record_list)

        # Start background stream
        threading.Thread(target=stream_worker, args=(phase_choice, stream_limit, record_list), daemon=True).start()
        
        # Wait for worker to finish
        # Wait for worker to finish
        print("Waiting for streaming to complete...")
        while streaming_active:
            time.sleep(0.2)

        # Give in-flight labels time to arrive before prompting
        print("Waiting for last labels to arrive...")
        time.sleep(3)

        print("\n" + "="*40)
        ready = input("Ready to generate testing log CSV? (y/n): ").lower()
        if ready == 'y':
            generate_testing_csv(phase_choice)
        else:
            print("Skipping CSV generation.")

        print("\nRestarting system...")