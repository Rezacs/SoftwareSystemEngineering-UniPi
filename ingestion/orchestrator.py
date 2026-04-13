from ingestion.record_receiver import RecordReceiver
from ingestion.raw_session_creator import RawSessionCreator
from ingestion.ingestion_system_config import IngestionSystemConfiguration
from ingestion.records_buffer import RecordsBuffer
import time
import pandas as pd
import requests
import json
import datetime
from flask import Flask, jsonify
from pathlib import Path
import socket
import sys


class IngestionSystemOrchestrator:

    def __init__(self,config_file_path = None):

        if config_file_path is None:
            config_file_path = Path(__file__).resolve().parents[1] / "config" / "ingestionConfig.json"


        self.log_file_path=Path(__file__).resolve().parents[1] / "logs" / "ingestionLog.json"

        try:

            with open(self.log_file_path, 'r') as f:
                self.log = json.load(f)

                
        except FileNotFoundError:
            print(f"[INFO] Log file not found at {self.log_file_path}. Starting with an empty log.")
            self.log = {}  # Initialize an empty default structure

        # 2. Catches if the file exists but has bad/empty JSON
        except json.JSONDecodeError as e:
            print(f"\n[WARNING] Log file is corrupted or empty: {e}")
            print("Falling back to an empty log to prevent a crash.")
            self.log = {}

        self.tmp_log=[]

        print(f"[INFO] Ingestion system orchestrator initialization...")

        self.ingestion_system_config = IngestionSystemConfiguration(config_file_path)

        self.receiver = RecordReceiver(self.ingestion_system_config.json_schema_path)

        print(f"[INFO] Record receiver initialized")

        self.raw_session_creator = RawSessionCreator(self.ingestion_system_config.sufficient_record_treshold)

        print(f"[INFO] Raw session creator initialized")

        self.records_buffer = RecordsBuffer("fscDB.db")

        if self.records_buffer.init_db():
            print(f"[INFO] Database correctly initialized")
        else:
            print("[ERROR] Error encountered initializing the database")
            exit(1)

        #Creation of url to speak with Evaluation system and preparation system
        self.evaluation_url=f"http://{self.ingestion_system_config.evaluation_system_ip}:{self.ingestion_system_config.evaluation_system_port}/{self.ingestion_system_config.evaluation_system_endpoint}"
        self.preparation_url=f"http://{self.ingestion_system_config.preparation_system_ip}:{self.ingestion_system_config.preparation_system_port}/{self.ingestion_system_config.preparation_system_endpoint}"

        self.app = Flask(__name__)

        self.app.add_url_rule('/run', methods=['POST'], view_func=self.run)

        print(f"[INFO] Flask service started initialized")

        print(f"""
               --- Ingestion System Configuration ---
               Phase:             {self.ingestion_system_config.phase}
               Thresholds:        Missing_Samples: {self.ingestion_system_config.missing_samples_treshold}, Sufficient_Records: {self.ingestion_system_config.sufficient_record_treshold}
               Evaluation System IP:PORT : {self.ingestion_system_config.evaluation_system_ip}:{self.ingestion_system_config.evaluation_system_port}
               Evaluation System endpoint : /{self.ingestion_system_config.evaluation_system_endpoint}
               Preparation System IP:PORT : {self.ingestion_system_config.preparation_system_ip}:{self.ingestion_system_config.preparation_system_port}
               Preparation System endpoint : /{self.ingestion_system_config.preparation_system_endpoint}
               --------------------------------------
        """)

    def log_event(self,event : dict):

        #event["timestamp"]=datetime.datetime.now().isoformat()

        self.tmp_log.append(event)

    def write_log_file(self,timestamp : datetime.datetime):

        self.log[f"{timestamp}"]=self.tmp_log

        with open(self.log_file_path, 'w') as file:
            json.dump(self.log, file, indent=4)

    def http_200_response(self):
        #If the record received are valid this is what the client side system will receive in every case
        return jsonify({"Message": "Data correctly received"}), 200
    
    def http_400_response(self):
        #If the record received isn't valid this is what the client side system will receive
        return jsonify({"Error": "Bad data"}), 400

    def run(self,input_path=None,output_path=None):


        if input_path is None:
            input_path = Path(__file__).resolve().parents[1] / "data" / "outputs" / "client_message.json"
        if output_path is None:
            output_path = Path(__file__).resolve().parents[1] / "data" / "outputs" / "raw_session.json"

        start_time=time.perf_counter()

        timestamp=datetime.datetime.now().isoformat()

        self.tmp_log=[]

        record = self.receiver.receive_record()

        if record is None:
            print(f"[INFO] : record received has invalid schema, discarded")
            return self.http_400_response()

        record = pd.DataFrame(record, index=[0]).reset_index(drop=True)

        if self.records_buffer.upsert_with_dataframe(record):
            end_time=time.perf_counter()
            event={
                "process" : "I0",
                "outcome" : "Record stored",
                "latency" : end_time-start_time
            }
            self.log_event(event)
            print(f"[INFO] Record inserted in the Buffer")
        else:
            print(f"[ERROR] Error occurred inserting the record in the buffer")
            return self.http_200_response()

        #Check if it is possible to create a raw session

        n_rows=self.records_buffer.getNumberOfAvailableRecords()
        print(f"[DEBUG] Available records in buffer: {n_rows}")
        if not self.raw_session_creator.isNumberOfRecordsSufficient(n_rows):
            end_time=time.perf_counter()
            event={
                "process" : "I1",
                "outcome" : "0-Not enough record to create a raw session",
                "latency" : end_time-start_time
            }
            self.log_event(event)
            self.write_log_file(timestamp)
            print(f"[INFO] Record stored, not enough record to create a raw session")
            return self.http_200_response()

        end_time=time.perf_counter()
        event={
                "process" : "I1",
                "outcome" : "1-Enough record to create a raw session",
                "latency" : end_time-start_time
        }
        self.log_event(event)
        #create raw session

        records,ids=self.records_buffer.retrieve_last_records()

        raw_session = self.raw_session_creator.create_raw_session(records)

        #mark missing samples and check if raw session is valid

        if self.raw_session_creator.mark_missing_samples(raw_session) > self.ingestion_system_config.missing_samples_treshold:
            end_time=time.perf_counter()
            event={
                "process" : "I2",
                "outcome" : "0-Invalid raw session, discarded",
                "latency" : end_time-start_time
            }
            self.log_event(event)
            self.write_log_file(timestamp)
            print(f"[INFO] Raw session discarded")
            return self.http_200_response()
        
        end_time=time.perf_counter()
        event={
                "process" : "I2",
                "outcome" : "1-Raw session is valid",
                "latency" : end_time-start_time
        }
        self.log_event(event)

        #check if is evaluation phase
        if self.ingestion_system_config.phase==1:
            #send label to evaluation system
            records = raw_session["records"]
            for record in records:
                
                json_label={"player_id" : record["player_id"],"label" : record["label"]}

                try:
                    print(f"Sending : {json_label}")
                    risp = requests.post(self.evaluation_url, json=json_label,timeout=10)

                    #risp.raise_for_status()

                    
                    end_time=time.perf_counter()
                    event={
                            "process" : "I3",
                            "phase" : 1,
                            "outcome" : "label sent to evaluation system",
                            "latency" : end_time-start_time
                    }
                    self.log_event(event)

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
                
                

        
        #send data preparation system
        try:
            print(f"Sending : {raw_session}")
            risp = requests.post(self.preparation_url, json=raw_session,timeout=10)

            #risp.raise_for_status()
            print(risp)

            
            end_time=time.perf_counter()
            event={
                    "process" : "I4",
                    "phase" : self.ingestion_system_config.phase,
                    "outcome" : "raw session sent to preparation system",
                     "latency" : end_time-start_time
            }
            timestamp=self.log_event(event)

            #write json log file
            self.write_log_file(timestamp)

            if not self.records_buffer.delete_records(ids):
                print(f"ERROR: an error occured extracting records from buffer")
                

            print(f"[INFO] Raw session correctly sent to preparation system")
        
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

        finally:
            pass

        return self.http_200_response()


    def check_ip_and_port(self):
    
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
                print(f"\nERROR: Network configuration issue!")
                print(f"Cannot bind to IP: '{target_ip}'. Make sure this IP belongs to your machine.")
                print(f"System details: {e}")
            
            print("Shutting down this system to prevent conflicts...\n")
            sys.exit(1)
        
    
    def start(self):
        """
        Start Flask server

        """

        print("[INFO] Starting Flask server...")

        self.check_ip_and_port()
            
        self.app.run(host=self.ingestion_system_config.hosting_ip, port=self.ingestion_system_config.hosting_port)
    
