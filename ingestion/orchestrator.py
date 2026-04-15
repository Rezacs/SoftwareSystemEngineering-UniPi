import concurrent.futures
import datetime
import json
import socket
import sys
import threading
import time
from pathlib import Path

import pandas as pd
import requests
from flask import Flask, jsonify

from ingestion.ingestion_system_config import IngestionSystemConfiguration
from ingestion.raw_session_creator import RawSessionCreator
from ingestion.record_receiver import RecordReceiver
from ingestion.records_buffer import RecordsBuffer


class IngestionSystemOrchestrator:
    """Orchestrates the data ingestion pipeline, handling record reception and session forwarding.

    This class acts as the central hub of the ingestion system. It sets up a Flask
    server to receive incoming data records, uses a thread pool to process them
    concurrently, stores them in an SQLite buffer, and forwards bundled raw sessions
    to the preparation and evaluation systems based on configuration limits.

    Attributes:
        log_file_path (Path): Path to the ingestion log JSON file.
        log (dict): In-memory representation of the event log.
        ingestion_system_config (IngestionSystemConfiguration): Configuration manager.
        receiver (RecordReceiver): Component responsible for validating incoming records.
        raw_session_creator (RawSessionCreator): Component responsible for bundling records.
        records_buffer (RecordsBuffer): Thread-safe SQLite database manager for stored records.
        evaluation_url (str): Endpoint URL for the evaluation system.
        preparation_url (str): Endpoint URL for the data preparation system.
        executor (concurrent.futures.ThreadPoolExecutor): Thread pool for concurrent processing.
        lock (threading.Lock): Thread lock for safe log file writing.
        app (Flask): The Flask web server application instance.
    """

    def __init__(self, config_file_path=None):
        """Initializes the orchestrator, its components, and the Flask application.

        Args:
            config_file_path (str or Path, optional): Path to the configuration
                JSON file. Defaults to None, which resolves to a default path.
        """

        if config_file_path is None:
            config_file_path = Path(__file__).resolve().parents[1] / "config" / "ingestionConfig.json"

        self.log_file_path = Path(__file__).resolve().parents[1] / "logs" / "ingestionLog.json"

        try:

            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                self.log = json.load(f)

        except FileNotFoundError:
            print(f"[INFO] Log file not found at {self.log_file_path}. Starting with an empty log.")
            self.log = {}  # Initialize an empty default structure

        # 2. Catches if the file exists but has bad/empty JSON
        except json.JSONDecodeError as e:
            print(f"\n[WARNING] Log file is corrupted or empty: {e}")
            print("Falling back to an empty log to prevent a crash.")
            self.log = {}

        print("[INFO] Ingestion system orchestrator initialization...")

        self.ingestion_system_config = IngestionSystemConfiguration(config_file_path)

        self.receiver = RecordReceiver(self.ingestion_system_config.json_schema_path)

        print("[INFO] Record receiver initialized")

        self.raw_session_creator = RawSessionCreator(self.ingestion_system_config.sufficient_record_threshold)

        print("[INFO] Raw session creator initialized")

        self.records_buffer = RecordsBuffer("fscDB.db")

        if self.records_buffer.init_db():
            print("[INFO] Database correctly initialized")
        else:
            print("[ERROR] Error encountered initializing the database")
            sys.exit(1)

        # Creation of url to speak with Evaluation system and preparation system
        self.evaluation_url = f"http://{self.ingestion_system_config.evaluation_system_ip}:{self.ingestion_system_config.evaluation_system_port}/{self.ingestion_system_config.evaluation_system_endpoint}"
        self.preparation_url = f"http://{self.ingestion_system_config.preparation_system_ip}:{self.ingestion_system_config.preparation_system_port}/{self.ingestion_system_config.preparation_system_endpoint}"

        print("[INFO] Initializing Thread pool")

        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.ingestion_system_config.number_of_threads)
        self.lock = threading.Lock()

        self.app = Flask(__name__)

        self.app.add_url_rule('/run', methods=['POST'], view_func=self.run)

        print("[INFO] Flask service initialized")

        print(f"\n"
              f"     --- Ingestion System Configuration ---\n"
              f"     Phase:             {self.ingestion_system_config.phase}\n"
              f"     Missing_Samples: {self.ingestion_system_config.missing_samples_threshold}, \n"
              f"     Sufficient_Records: {self.ingestion_system_config.sufficient_record_threshold} \n"
              f"     Evaluation System IP:PORT : {self.ingestion_system_config.evaluation_system_ip}:{self.ingestion_system_config.evaluation_system_port}\n"
              f"     Evaluation System endpoint : /{self.ingestion_system_config.evaluation_system_endpoint}\n"
              f"     Preparation System IP:PORT : {self.ingestion_system_config.preparation_system_ip}:{self.ingestion_system_config.preparation_system_port}\n"
              f"     Preparation System endpoint : /{self.ingestion_system_config.preparation_system_endpoint}\n"
              f"     --------------------------------------\n"
              f"        ")

    def write_log_file(self, log: list, timestamp: str):
        """Thread-safely writes processing event logs to the JSON log file.

        Args:
            log (list): A list of dictionaries representing individual event logs.
            timestamp (str): The ISO formatted timestamp string serving as the
                key for this specific log entry.
        """
        # Thread safe using lock
        with self.lock:
            self.log[f"{timestamp}"] = log

            with open(self.log_file_path, 'w', encoding='utf-8') as file:
                json.dump(self.log, file, indent=4)

    def http_200_response(self):
        """Returns a standardized HTTP 200 Success response for the client.

        Returns:
            tuple: A Flask JSON response and a 200 HTTP status code.
        """
        # If the record received are valid this is what the client side system will receive in every case
        return jsonify({"Message": "Data correctly received"}), 200

    def http_400_response(self):
        """Returns a standardized HTTP 400 Bad Request response for the client.

        Returns:
            tuple: A Flask JSON response and a 400 HTTP status code.
        """
        # If the record received isn't valid this is what the client side system will receive
        return jsonify({"Error": "Bad data"}), 400

    def _process(self, start_time: float, timestamp: str, record: dict):
        """Asynchronously processes an accepted record, updating the buffer and forwarding sessions.

        Upserts the record into the database. If enough records exist to meet the threshold,
        bundles them into a raw session. Validates the session, and if valid, sends labels to
        the evaluation system (if in Phase 1) and forwards the full session to the preparation system.

        Args:
            start_time (float): The performance counter start time of the request.
            timestamp (str): The ISO formatted timestamp of the request.
            record (dict): The validated incoming data record.

        Returns:
            tuple or None: A Flask response if an error occurs during buffer insertion,
                otherwise implicitly returns None when finished.
        """
        tmp_log = []

        record = pd.DataFrame(record, index=[0]).reset_index(drop=True)

        if self.records_buffer.upsert_with_dataframe(record):
            end_time = time.perf_counter()
            event = {
                "process": "I0",
                "outcome": "Record stored",
                "latency": end_time - start_time
            }
            tmp_log.append(event)
            print("[INFO] Record inserted in the Buffer")
        else:
            print("[ERROR] Error occurred inserting the record in the buffer")
            return

        # Check if it is possible to create a raw session

        n_rows = self.records_buffer.get_number_of_available_records()
        print(f"[DEBUG] Available records in buffer: {n_rows}")
        if not self.raw_session_creator.is_number_of_records_sufficient(n_rows):
            end_time = time.perf_counter()
            event = {
                "process": "I1",
                "outcome": "0-Not enough record to create a raw session",
                "latency": end_time - start_time
            }
            tmp_log.append(event)
            self.write_log_file(tmp_log, timestamp)
            print("[INFO] Record stored, not enough record to create a raw session")
            return

        end_time = time.perf_counter()
        event = {
            "process": "I1",
            "outcome": "1-Enough record to create a raw session",
            "latency": end_time - start_time
        }
        tmp_log.append(event)
        # create raw session

        with self.lock:
            records, ids = self.records_buffer.extract_last_records()

        raw_session = self.raw_session_creator.create_raw_session(records)

        # mark missing samples and check if raw session is valid

        if self.raw_session_creator.mark_missing_samples(raw_session) > self.ingestion_system_config.missing_samples_threshold:
            end_time = time.perf_counter()
            event = {
                "process": "I2",
                "outcome": "0-Invalid raw session, discarded",
                "latency": end_time - start_time
            }
            tmp_log.append(event)
            self.write_log_file(tmp_log, timestamp)
            print("[INFO] Raw session discarded")
            return

        end_time = time.perf_counter()
        event = {
            "process": "I2",
            "outcome": "1-Raw session is valid",
            "latency": end_time - start_time
        }
        tmp_log.append(event)

        # check if is evaluation phase
        if self.ingestion_system_config.phase == 1:
            # send label to evaluation system
            records = raw_session["records"]
            for r in records:

                json_label = {"player_id": r["player_id"], "label": r["label"]}

                try:
                    print(f"Sending : {json_label}")
                    risp = requests.post(self.evaluation_url, json=json_label, timeout=10)

                    # risp.raise_for_status()

                    end_time = time.perf_counter()
                    event = {
                        "process": "I3",
                        "phase": 1,
                        "outcome": "label sent to evaluation system",
                        "latency": end_time - start_time
                    }
                    tmp_log.append(event)

                except requests.exceptions.Timeout:
                    error_msg = f"Connection to {self.evaluation_url} timed out after 10 seconds."
                    print(f"\nERROR: {error_msg}")

                except requests.exceptions.ConnectionError:
                    error_msg = f"Could not connect to {self.evaluation_url}. Is it running?"
                    print(f"\nERROR: {error_msg}")

                except requests.exceptions.HTTPError as http_err:
                    print(f"\nERROR: The server returned an HTTP error: {http_err}")

                except requests.exceptions.RequestException as e:
                    print(f"\nERROR: An unexpected network error occurred: {e}")

        # send data preparation system
        try:
            # print(f"Sending : {raw_session}")
            risp = requests.post(self.preparation_url, json=raw_session, timeout=10)

            # risp.raise_for_status()
            print(risp)

            if risp.status_code != 200:
                print(f"[WARNING] Request failed with status code: {risp.status_code}")
                print(f"          Server response details: {risp.text}")
                self.records_buffer.upsert_with_dataframe(records)
            else:

                end_time = time.perf_counter()
                event = {
                    "process": "I4",
                    "phase": self.ingestion_system_config.phase,
                    "outcome": "raw session sent to preparation system",
                    "latency": end_time - start_time
                }
                tmp_log.append(event)

                # write json log file
                self.write_log_file(tmp_log, timestamp)

            #if not self.records_buffer.delete_records(ids):
            #    print("ERROR: an error occurred extracting records from buffer")

                print("[INFO] Raw session correctly sent to preparation system")

        except requests.exceptions.Timeout:
            print(f"\nERROR: Connection to {self.preparation_url} timed out after 10 seconds.")

        except requests.exceptions.ConnectionError:
            print(f"\nERROR: Could not connect to {self.preparation_url}. Is the evaluation server running?")

        except requests.exceptions.HTTPError as http_err:
            print(f"\nERROR: The server returned an HTTP error: {http_err}")
            # Printing the text often reveals the exact error message the server sent back
            print(f"Server message: {risp.text}")

        except requests.exceptions.RequestException as e:
            # This is the base class for all requests exceptions. It acts as a safety net.
            print(f"\nERROR: An unexpected network error occurred: {e}")

    def run(self, input_path=None, output_path=None):
        """Flask route handler to receive and queue a new record for processing.

        This method acts as the entry point for incoming HTTP requests. It validates
        the incoming record scheme and, if valid, delegates the actual processing
        to a worker thread in the thread pool.

        Args:
            input_path (str, optional): Unused path argument. Defaults to None.
            output_path (str, optional): Unused path argument. Defaults to None.

        Returns:
            tuple: An HTTP response indicating success (200) if the record was
                accepted, or failure (400) if the schema was invalid.
        """
        if input_path is None:
            input_path = Path(__file__).resolve().parents[1] / "data" / "outputs" / "client_message.json"
        if output_path is None:
            output_path = Path(__file__).resolve().parents[1] / "data" / "outputs" / "raw_session.json"

        start_time = time.perf_counter()

        timestamp = datetime.datetime.now().isoformat()

        record = self.receiver.receive_record()

        if record is None:
            print("[INFO] : record received has invalid schema, discarded")
            return self.http_400_response()

        # awake a Thread from the pool
        self.executor.submit(self._process, start_time, timestamp, record)

        return self.http_200_response()

    def check_ip_and_port(self):
        """Verifies that the configured IP and port are available for the Flask server.

        Creates a dummy network socket to test the connection. If the port is
        already in use, it safely terminates the program to prevent conflicts.

        Raises:
            SystemExit: If the target port is already in use or cannot be bound.
        """
        target_ip = self.ingestion_system_config.hosting_ip
        target_port = self.ingestion_system_config.hosting_port

        # 1. Create a dummy network socket
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            # 2. Attempt to bind to the IP and Port
            test_socket.bind((target_ip, target_port))

            # 3. If it succeeds, the port is free!
            #  close test socket so Flask can use it.
            test_socket.close()

        except OSError as e:
            # e.winerror is specific to Windows. For Linux/Mac, you'd use e.errno == 98 / 99
            if getattr(e, 'winerror', e.errno) in (10048, 98):
                print(f"\nERROR: Port {target_port} is already in use!")
            else:
                print("\nERROR: Network configuration issue!")
                print(f"Cannot bind to IP: '{target_ip}'. Make sure this IP belongs to your machine.")
                print(f"System details: {e}")

            print("Shutting down this system to prevent conflicts...\n")
            sys.exit(1)

    def start(self):
        """Starts the Flask web server to begin listening for incoming records."""
        print("[INFO] Starting Flask server...")

        self.check_ip_and_port()

        self.app.run(host=self.ingestion_system_config.hosting_ip, port=self.ingestion_system_config.hosting_port)
