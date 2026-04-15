import concurrent.futures
import datetime
import json
import socket
import sys
import threading
import time
from pathlib import Path

import requests
from flask import Flask, jsonify

from preparation.preparation_system_config import PreparationSystemConfiguration
from preparation.prepared_session_creator import PreparedSessionCreator
from preparation.raw_session_receiver import RawSessionReceiver


class PreparationSystemOrchestrator:
    """Orchestrates the preparation system pipeline and handles network routing.

    This class sets up a Flask server to receive raw sessions, processes them
    concurrently using a thread pool, runs them through the data preparation
    pipeline (cleaning, imputing, feature extraction), un-batches the records,
    and forwards the individual prepared sessions to either the segregation
    system (Phase 0) or the classification system (Phase 1).

    Attributes:
        log_file_path (Path): Path to the preparation event log JSON file.
        log (dict): In-memory dictionary holding the event logs.
        preparation_system_config (PreparationSystemConfiguration): System configurations.
        raw_session_receiver (RawSessionReceiver): Validates incoming JSON schemas.
        prepared_session_creator (PreparedSessionCreator): Handles data transformations.
        segregation_url (str): Endpoint URL for the segregation system.
        classification_url (str): Endpoint URL for the classification system.
        executor (concurrent.futures.ThreadPoolExecutor): Thread pool for background tasks.
        lock (threading.Lock): Mutex lock for safe, concurrent log writing.
        app (Flask): The underlying Flask web application.
    """

    def __init__(self, config_file_path: str = None):
        """Initializes the orchestrator, its components, and the Flask application.

        Args:
            config_file_path (str, optional): Path to the configuration JSON file.
                If None, resolves to a default path in the config directory.
        """
        if config_file_path is None:
            config_file_path = Path(__file__).resolve().parents[1] / "config" / "preparationConfig.json"

        self.log_file_path = Path(__file__).resolve().parents[1] / "logs" / "preparationLog.json"

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

        print("[INFO] Preparation system orchestrator initialization...")

        self.preparation_system_config = PreparationSystemConfiguration(config_file_path)

        print(f"""
               --- Preparation System Configuration ---
               Phase:             {self.preparation_system_config.phase}
               Classification System IP:PORT : {self.preparation_system_config.classification_system_ip}:{self.preparation_system_config.classification_system_port}
               Classification System endpoint : /{self.preparation_system_config.classification_system_endpoint}
               Segregation System IP:PORT : {self.preparation_system_config.segregation_system_ip}:{self.preparation_system_config.segregation_system_port}
               Segregation System endpoint: {self.preparation_system_config.segregation_system_endpoint}
               --------------------------------------
        """)

        self.raw_session_receiver = RawSessionReceiver(self.preparation_system_config.json_schema_path)

        print("[INFO] Raw session receiver initialized")

        self.prepared_session_creator = PreparedSessionCreator()

        self.segregation_url = f"http://{self.preparation_system_config.segregation_system_ip}:{self.preparation_system_config.segregation_system_port}/{self.preparation_system_config.segregation_system_endpoint}"
        self.classification_url = f"http://{self.preparation_system_config.classification_system_ip}:{self.preparation_system_config.classification_system_port}/{self.preparation_system_config.classification_system_endpoint}"

        print("[INFO] Initializing Thread pool")

        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.preparation_system_config.number_of_threads)
        self.lock = threading.Lock()

        print("[INFO] Prepared session creator initialized")

        self.app = Flask(__name__)

        self.app.add_url_rule('/run', methods=['POST'], view_func=self.run)

        print("[INFO] Flask service started initialized")

    def write_log_file(self, log: list, timestamp: str):
        """Thread-safely writes processing event logs to the JSON log file.

        Args:
            log (list): A list of dictionary objects representing processing events.
            timestamp (str): The ISO formatted timestamp used as the key for the log entry.
        """
        # Thread safe using lock
        with self.lock:
            self.log[f"{timestamp}"] = log

            with open(self.log_file_path, 'w', encoding='utf-8') as file:
                json.dump(self.log, file, indent=4)

    def http_200_response(self):
        """Returns a standardized HTTP 200 Success response.

        Returns:
            tuple: A Flask JSON response and a 200 HTTP status code.
        """
        # If the record received are valid this is what the client side system will receive in every case
        return jsonify({"Message": "Data correctly received"}), 200

    def http_400_response(self):
        """Returns a standardized HTTP 400 Bad Request response.

        Returns:
            tuple: A Flask JSON response and a 400 HTTP status code.
        """
        # If the record received isn't valid this is what the client side system will receive
        return jsonify({"Error": "Raw session received has an invalid schema"}), 400

    def _process(self, start_time: float, timestamp: str, raw_session: dict):
        """Asynchronously processes a raw session and forwards the prepared data.

        This method applies the data preparation pipeline (cleaning, imputing,
        clipping outliers, extracting features) to the batch session. It then
        un-batches the results into individual prepared sessions and routes them
        to the appropriate downstream system based on the current phase.

        Args:
            start_time (float): The performance counter start time of the request.
            timestamp (str): The ISO formatted timestamp of the request.
            raw_session (dict): The incoming raw session payload.
        """
        tmp_log = []

        # Create prepared session
        raw_session = self.prepared_session_creator.parse_raw_session(raw_session)

        # Correct missing samples
        raw_session = self.prepared_session_creator.correct_missing_samples(raw_session)

        if raw_session is None:
            print("[INFO] Raw session discarded due too many errors")
            return

        # Correct outliers
        raw_session = self.prepared_session_creator.correct_absolute_outliers(raw_session)

        # Extract features
        batch_prepared_session = self.prepared_session_creator.extract_features(raw_session)

        # LOGIC TO DECOMPOSE THE BATCH
        features = batch_prepared_session.get("features")
        prepared_sessions = []
        for d in features:
            prepared_session = {
                "session_id": batch_prepared_session.get("UUID"),
                "player_id": d.get("player_id"),
                "skill_overall": d.get("skill_overall"),
                "social_influence_score": d.get("social_influence_score"),
                "injuries_impact_score": d.get("injuries_impact_score"),
                "label": d.get("label")
            }
            prepared_sessions.append(prepared_session)

        if self.preparation_system_config.phase == 0:

            for p in prepared_sessions:
                # Development phase
                # Send to segregation system
                try:
                    print(f"sending : {p}")
                    risp = requests.post(self.segregation_url, json=p, timeout=2)
                    print(risp)

                    end_time = time.perf_counter()
                    event = {
                        "process": "X1",
                        "phase": 0,
                        "outcome": "prepared session sent to segregation system",
                        "latency": end_time - start_time
                    }
                    tmp_log.append(event)

                except requests.exceptions.Timeout:
                    print(f"\nERROR: Connection to {self.segregation_url} timed out after 3 seconds.")

                except requests.exceptions.ConnectionError:
                    print(f"\nERROR: Could not connect to {self.segregation_url}. Is the segregation system running?")

                except requests.exceptions.HTTPError as http_err:
                    print(f"\nERROR: The server returned an HTTP error: {http_err}")
                    print(f"Server message: {risp.text}")

                except requests.exceptions.RequestException as e:
                    # This is the base class for all requests exceptions. It acts as a safety net.
                    print(f"\nERROR: An unexpected network error occurred: {e}")

            self.write_log_file(tmp_log, timestamp)

            return

        for p in prepared_sessions:
            # Evaluation phase send to classification system
            try:
                print(f"sending : {p}")
                risp = requests.post(self.classification_url, json=p,timeout=2)
                print(risp)

                end_time = time.perf_counter()
                event = {
                    "process": "X2",
                    "phase": 1,
                    "outcome": "prepared session sent to classification system",
                    "latency": end_time - start_time
                }

                tmp_log.append(event)

            except requests.exceptions.Timeout:
                print(f"\nERROR: Connection to {self.classification_url} timed out after 3 seconds.")

            except requests.exceptions.ConnectionError:
                print(
                    f"\nERROR: Could not connect to {self.classification_url}. Is the classification system running?")

            except requests.exceptions.HTTPError as http_err:
                print(f"\nERROR: The server returned an HTTP error: {http_err}")
                print(f"Server message: {risp.text}")

            except requests.exceptions.RequestException as e:
                # This is the base class for all requests exceptions. It acts as a safety net.
                print(f"\nERROR: An unexpected network error occurred: {e}")

        self.write_log_file(tmp_log, timestamp)

    def run(self):
        """Flask route handler to receive and process incoming raw sessions.

        This method intercepts HTTP POST requests, delegates validation to the
        RawSessionReceiver, and submits valid payloads to the thread pool for
        asynchronous processing.

        Returns:
            tuple: An HTTP response indicating success (200) or schema failure (400).
        """
        start_time = time.perf_counter()

        timestamp = datetime.datetime.now().isoformat()

        # Receive raw session
        raw_session = self.raw_session_receiver.receive_raw_session()

        if raw_session is None:
            print("[INFO] : Raw session received has invalid schema, discarded")
            return self.http_400_response()

        # awake a Thread from the pool
        self.executor.submit(self._process, start_time, timestamp, raw_session)

        return self.http_200_response()

    def check_ip_and_port(self):
        """Verifies that the configured IP and port are available for the server.

        Creates a dummy network socket to test the connection.

        Raises:
            SystemExit: If the target port is already in use or cannot be bound,
                safely terminating the system to prevent conflicts.
        """
        target_ip = self.preparation_system_config.hosting_ip
        target_port = self.preparation_system_config.hosting_port

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
        """Starts the Flask web server to begin listening for incoming sessions."""
        print("Starting Flask server...")

        self.check_ip_and_port()

        self.app.run(host=self.preparation_system_config.hosting_ip, port=self.preparation_system_config.hosting_port)
