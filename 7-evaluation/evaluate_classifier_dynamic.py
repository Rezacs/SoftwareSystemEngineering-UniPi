import json
import time
import os
import requests

# --- CONFIGURATION ---
TARGET_URL = "http://127.0.0.1:8001/evaluation"
INGESTION_FILE = "ingestion_to_evaluation.json"
CLASSIFICATION_FILE = "classification_to_evaluation.json"

def read_and_send_payload(file_path, source_name):
    """Reads the JSON file and transmits it to the Evaluation API."""
    try:
        # Give the upstream system a tiny fraction of a second to finish saving the file
        time.sleep(0.5)
        
        with open(file_path, 'r') as f:
            payload = json.load(f)
            
        # If the file accidentally contains a list with one item, extract it
        if isinstance(payload, list) and len(payload) > 0:
            payload = payload[0]
            
        response = requests.post(TARGET_URL, json=payload)
        
        if response.status_code in [200, 201]:
            print(f"[{source_name}] Transmitted {payload.get('player_id')} successfully.")
        else:
            print(f"[{source_name}] Failed to transmit {payload.get('player_id')}. HTTP Status: {response.status_code}")
            
    except json.JSONDecodeError:
        print(f"[{source_name}] Warning: File is currently being written to or is empty. Retrying next cycle.")
    except requests.exceptions.ConnectionError:
        print(f"[{source_name}] ERROR: Connection refused at {TARGET_URL}. Is the Evaluation System running?")
    except Exception as e:
        print(f"[{source_name}] Unexpected error: {e}")

def watch_data_pipes():
    """Continuously monitors the JSON files for updates and streams new data."""
    
    # Store the last modified time of the files
    last_ingestion_time = 0
    last_classification_time = 0
    
    print(f"Monitoring '{INGESTION_FILE}' and '{CLASSIFICATION_FILE}' for updates...")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            # 1. Check Ingestion File
            if os.path.exists(INGESTION_FILE):
                current_ingestion_time = os.path.getmtime(INGESTION_FILE)
                if current_ingestion_time > last_ingestion_time:
                    read_and_send_payload(INGESTION_FILE, "INGESTION")
                    last_ingestion_time = current_ingestion_time

            # 2. Check Classification File
            if os.path.exists(CLASSIFICATION_FILE):
                current_classification_time = os.path.getmtime(CLASSIFICATION_FILE)
                if current_classification_time > last_classification_time:
                    read_and_send_payload(CLASSIFICATION_FILE, "CLASSIFICATION")
                    last_classification_time = current_classification_time

            # Sleep for 1 second before checking again so we don't overload the CPU
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping DataOps Watcher.")

if __name__ == "__main__":
    print("=====================================================")
    print(" Starting DataOps File Watcher")
    print(" Target URL:", TARGET_URL)
    print("=====================================================\n")
    
    # Ensure the files exist before we start watching them
    if not os.path.exists(INGESTION_FILE):
        with open(INGESTION_FILE, 'w') as f: json.dump({}, f)
    if not os.path.exists(CLASSIFICATION_FILE):
        with open(CLASSIFICATION_FILE, 'w') as f: json.dump({}, f)
        
    watch_data_pipes()