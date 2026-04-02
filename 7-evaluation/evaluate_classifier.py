import json
import time
import random
import threading
import requests

# --- CONFIGURATION ---
TARGET_URL = "http://127.0.0.1:8001/evaluation"
INGESTION_FILE = "ingestion_to_evaluation.json"
CLASSIFICATION_FILE = "classification_to_evaluation.json"

def send_payload(source_name, payload):
    """Transmits a single JSON payload to the target REST API."""
    try:
        response = requests.post(TARGET_URL, json=payload)
        if response.status_code in [200, 201]:
            print(f"[{source_name}] Transmitted {payload['player_id']} successfully.")
        else:
            print(f"[{source_name}] Failed to transmit {payload['player_id']}. HTTP Status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"[{source_name}] ERROR: Connection refused at {TARGET_URL}. Is the Evaluation System running?")

def stream_data(source_name, file_path):
    """Reads a JSON file and streams the records to the API with realistic network delays."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[{source_name}] Critical Error: Could not locate data file -> {file_path}")
        return

    print(f"[{source_name}] Initiating data stream ({len(data)} records)...")
    
    for item in data:
        # Minor delay to mimic real asynchronous network traffic from different microservices
        time.sleep(random.uniform(0.5, 2.0))
        send_payload(source_name, item)
        
    print(f"[{source_name}] Data stream completed.")

if __name__ == "__main__":
    print("=====================================================")
    print(" Starting Microservice Data Feeder")
    print(" Target URL:", TARGET_URL)
    print("=====================================================\n")
    
    # Initialize separate threads for the Ingestion and Classification streams
    ingestion_thread = threading.Thread(target=stream_data, args=("INGESTION", INGESTION_FILE))
    classification_thread = threading.Thread(target=stream_data, args=("CLASSIFICATION", CLASSIFICATION_FILE))
    
    # Begin streaming
    ingestion_thread.start()
    classification_thread.start()
    
    # Keep the main process alive until both streams finish
    ingestion_thread.join()
    classification_thread.join()
    
    print("\n=====================================================")
    print(" Data Feeding Process Concluded.")
    print("=====================================================")