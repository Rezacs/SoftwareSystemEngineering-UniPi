import json
import time
import random
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
import pandas as pd
import requests

app = Flask(__name__)

# Volatile storage
results_storage = {}
streaming_active = False  # Flag to track background worker status

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

def generate_testing_csv(current_phase):
    print("\n[SYSTEM] Aggregating logs for performance analysis...")
    
    shared_logs = ["clientsideLogs.json", "ingestionLog.json", "preparationLog.json"]
    if current_phase == "0":
        target_logs = shared_logs + ["segregationLog.json", "developmentLog.json"]
    else:
        target_logs = shared_logs + ["productionLog.json", "evaluationLog.json"]

    aggregated_data = {}

    for log_file in target_logs:
        path = LOG_DIR / log_file
        if not path.exists():
            print(f"Warning: {log_file} not found in logs folder.")
            continue
            
        with path.open('r', encoding='utf-8') as f:
            try:
                entries = json.load(f)
                for entry in entries:
                    p_id = entry.get("player_id")
                    if not p_id: continue
                    
                    if p_id not in aggregated_data:
                        aggregated_data[p_id] = {"player_id": p_id}
                    
                    column_name = log_file.replace(".json", "_ts")
                    aggregated_data[p_id][column_name] = entry.get("timestamp")
            except Exception as e:
                print(f"Error reading {log_file}: {e}")

    if aggregated_data:
        test_df = pd.DataFrame(aggregated_data.values())
        output_path = LOG_DIR / "testing_log.csv"
        test_df.to_csv(output_path, index=False)
        print(f"SUCCESS: Testing log saved to {output_path}")
    else:
        print("FAILED: No matching player data found across logs.")

##########################################
# STREAMING WORKER
##########################################

def stream_worker(current_phase, limit, data_pool):
    global streaming_active
    streaming_active = True
    
    ingestion_cfg = config['network']['ingestion_system']
    url = f"http://{ingestion_cfg['ip']}:{ingestion_cfg['port']}{ingestion_cfg['endpoint']}"
    total_available = len(data_pool)

    for i in range(limit):
        index = i % total_available
        record = data_pool.iloc[index].to_dict()
        p_id = record.get('player_id')
        
        # Log the outgoing record
        log_event("clientsideLogs.json", {
            "player_id": p_id, 
            "timestamp": datetime.now().isoformat(), 
            "event": "sent"
        })
        
        try:
            requests.post(url, json=record, timeout=5)
            print(f"Sent [{i+1}/{limit}]: {p_id}")
        except:
            print(f"Target {url} unreachable.")

        time.sleep(random.uniform(2, 5))
    
    print("\n[SYSTEM] Sequence finished.")
    streaming_active = False

##########################################
# FLASK INTERFACE
##########################################

@app.route("/receive-label", methods=["POST"])
def receive_label():
    data = request.get_json()
    p_id = data.get("player_id")
    results_storage[p_id] = data
    return jsonify({"status": "received"})

def run_flask():
    app.run(host=config['network']['listen_host'], 
            port=config['network']['listen_port'], 
            use_reloader=False)

##########################################
# MAIN CONTROL LOOP
##########################################

if __name__ == "__main__":
    # Start Flask in a non-blocking thread so the console stays interactive
    threading.Thread(target=run_flask, daemon=True).start()
    
    while True:
        log_event("clientsideLogs.json", {"event": "launch", "timestamp": datetime.now().isoformat()})
        
        print("\n" + "="*40)
        print("CLIENT SYSTEM CONTROL PANEL")
        print("="*40)
        
        phase_choice = input("Select Phase: [0] Development, [1] Production: ")
        stream_limit = int(input("Enter number of records to stream: "))

        # Prepare Data
        pool_list = []
        if phase_choice == "0":
            for file_path in config['paths']['dev_files']:
                candidate_path = Path(file_path)
                if not candidate_path.is_absolute():
                    candidate_path = (REPO_ROOT / candidate_path).resolve()
                if candidate_path.exists():
                    df = pd.read_csv(candidate_path)
                    if 'id_player' in df.columns: df = df.rename(columns={'id_player': 'player_id'})
                    pool_list.append(df)
            data_pool = pd.concat(pool_list, axis=0, ignore_index=True)
        else:
            prod_path = Path(config['paths']['prod_file'])
            if not prod_path.is_absolute():
                prod_path = (REPO_ROOT / prod_path).resolve()
            data_pool = pd.read_csv(prod_path)
        
        data_pool = data_pool.where(pd.notnull(data_pool), None).sample(frac=1).reset_index(drop=True)

        # Start background stream
        threading.Thread(target=stream_worker, args=(phase_choice, stream_limit, data_pool), daemon=True).start()

        # Wait for worker to finish
        print("Waiting for streaming to complete...")
        while streaming_active:
            time.sleep(1)

        # Final Prompt
        ready = input("\nStreaming done. Are you ready to plot the logs? (y/n): ").lower()
        if ready == 'y':
            generate_testing_csv(phase_choice)
        else:
            print("Skipping CSV generation.")
            
        print("\nRestarting system...")