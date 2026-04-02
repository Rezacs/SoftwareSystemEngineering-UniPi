"""
    Evaluation System Orchestrator : loads all configs and runs the listening server
"""
import json
import logging
import threading
import os
import random
import sqlite3
import datetime
from src.utility.json_validation import validate_json_data_file
from src.utility import data_folder
from src.comms import ServerREST
from src.comms.json_transfer_api import ReceiveJsonApi, HumanDecisionApi
from src.player_store_controller import PlayerStoreController
from src.evaluation_report_controller import EvaluationReportController

CONFIG_PATH_REL = "configs/eval_config.json"
CONFIG_SCHEMA_PATH_REL = "schema/eval_config_schema.json"

IP_PATH_REL = "configs/eval_ip_config.json"
IP_PATH_SCHEMA_REL = "schema/eval_ip_config_schema.json"

LABEL_PATH_SCHEMA_REL = "schema/eval_label_input_schema.json"


class EvaluationSystemOrchestrator:
    """
    Orchestrator class for all Evaluation System functions
    """

    def __init__(self, service_mode=False):
        self.player_store_controller = PlayerStoreController()
        self.evaluation_report_controller = EvaluationReportController()
        self.config = None
        self.ip_config = None
        self.server = None
        self.service_mode = service_mode
        
        # STATE LOCK VARS FOR MODULE 6
        self.waiting_for_human = False
        self.current_pending_batch = None

    def load_config(self):
        config_path = os.path.join(data_folder, CONFIG_PATH_REL)
        with open(config_path, "r", encoding="UTF-8") as file:
            self.config = json.load(file)
        if not validate_json_data_file(self.config, CONFIG_SCHEMA_PATH_REL):
            logging.error("Invalid evaluation config file.")
            raise ValueError("Evaluation config validation failed.")

    def load_ip_config(self):
        ip_path = os.path.join(data_folder, IP_PATH_REL)
        with open(ip_path, "r", encoding="UTF-8") as file:
            self.ip_config = json.load(file)
        if not validate_json_data_file(self.ip_config, IP_PATH_SCHEMA_REL):
            logging.error("Invalid IP config file.")
            raise ValueError("IP config validation failed.")

    def create_tables(self):
        query_expert = """
            CREATE TABLE IF NOT EXISTS expertLabelTable (
                player_id TEXT,
                rating INTEGER,
                source TEXT
            )
        """
        query_classifier = """
            CREATE TABLE IF NOT EXISTS classifierLabelTable (
                player_id TEXT,
                rating INTEGER,
                source TEXT,
                classifier_id TEXT 
            )
        """
        self.player_store_controller.store.ps_create_table(query_expert)
        self.player_store_controller.store.ps_create_table(query_classifier)

    def handle_expert_message(self, label_dict):
        """Handler for data arriving from the Ingestion System"""
        self.load_config()

        # Prevent new data from processing if we are waiting for a human
        if self.waiting_for_human:
            print(f"[WARNING] Buffer locked. Waiting for decision on {self.current_pending_batch}. Ignoring new expert payload.")
            return False
            
        label_dict['source'] = 'expert'
        self.player_store_controller.save_label_prompt_eval(label_dict, self.config)
        
        # Check if the batch is complete
        self._check_and_trigger_batch(label_dict.get('player_id', 'UNKNOWN_PLAYER'))
        return True

    def handle_classifier_message(self, label_dict):
        """Handler for data arriving from the Classification System"""
        self.load_config()

        # Prevent new data from processing if we are waiting for a human
        if self.waiting_for_human:
            print(f"[WARNING] Buffer locked. Waiting for decision on {self.current_pending_batch}. Ignoring new classifier payload.")
            return False
            
        label_dict['source'] = 'classifier'
        self.player_store_controller.save_label_prompt_eval(label_dict, self.config)
        
        # Check if the batch is complete (Classifier might be the last one to arrive!)
        self._check_and_trigger_batch(label_dict.get('player_id', 'UNKNOWN_PLAYER'))
        return True

    def _check_and_trigger_batch(self, player_id):
        """Helper method to check batch size using complete pairs and trigger reports"""
        conn = sqlite3.connect(self.player_store_controller.db_path)
        cursor = conn.cursor()
        
        # Count only players that have BOTH an expert and a classifier label
        query = """
            SELECT COUNT(DISTINCT e.player_id) 
            FROM expertLabelTable e
            INNER JOIN classifierLabelTable c ON e.player_id = c.player_id
        """
        cursor.execute(query)
        complete_pairs_count = cursor.fetchone()[0]
        conn.close()
        
        BATCH_SIZE = self.config.get("evaluation_batch_size", 5) 
        
        if complete_pairs_count >= BATCH_SIZE:
            batch_name = f"Batch_{player_id}"
            print(f"\nSufficient COMPLETE pairs reached (Batch of {BATCH_SIZE}). Triggering report...")
            
            self.evaluation_report_controller.generate_human_report(
                batch_name=batch_name, 
                eval_config=self.config
            )
            
            print("Executing BPMN Task: REMOVE LABELS (Clearing Batch)...")
            self.player_store_controller.remove_labels(player_id) 
            
            if self.service_mode:
                print(f"[SERVICE MODE ON] Statistically generating Human Decision...")
                self.waiting_for_human = True
                self.current_pending_batch = batch_name
                simulated_decision = random.random() < 0.8 
                self.submit_human_decision(batch_name, simulated_decision)
            else:
                self.waiting_for_human = True
                self.current_pending_batch = batch_name
                print(f"\n[SYSTEM PAUSED] Batch evaluation complete.")
                print(f"Waiting for Human Manager to review report and submit decision to /evaluation/decision")
                print(f"Expected Payload: {{'batch_id': '{batch_name}', 'accept': true/false}}\n")

    def handle_human_decision_payload(self, decision_dict):
        batch_id = decision_dict.get("batch_id", "Unknown_Batch")
        is_accepted = decision_dict.get("accept")
        
        print(f"\n[HUMAN INPUT RECEIVED] Decision for {batch_id}: {'ACCEPT' if is_accepted else 'REJECT'}")
        self.submit_human_decision(batch_id=batch_id, classifier_is_good=is_accepted)
        return True

    def submit_human_decision(self, batch_id, classifier_is_good):
        if not self.waiting_for_human or self.current_pending_batch != batch_id:
            print(f"\n[ERROR] Invalid request. System is not currently waiting for a decision on {batch_id}.")
            return False

        print(f"\n--- Processing Human Decision for Batch: {batch_id} ---")
        
        if classifier_is_good:
            print("Decision: YES (Classifier evaluated as GOOD). Process Complete.")
            print("[SYSTEM] Classifier validated successfully. No further action required.")
        else:
            print("Decision: NO (Classifier evaluated as BAD).")
            print("Executing BPMN Task: Generating configuration for Messaging System...")
            
            report_path = os.path.join(data_folder, "reports", f"{batch_id}.json")
            classifier_id = "UNKNOWN"
            metrics = {}
            
            if os.path.exists(report_path):
                with open(report_path, 'r') as f:
                    report_data = json.load(f)
                    classifier_id = report_data.get("classifier_id", "UNKNOWN")
                    metrics = report_data.get("metrics", {})
            
            recalibration_config = {
                "event": "CLASSIFIER_REJECTED",
                "classifier_id": classifier_id,
                "batch_id": batch_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "action_required": "RECALIBRATE",
                "reason": "Human evaluator rejected classification based on excessive errors.",
                "failure_metrics": metrics
            }
            
            print("\n[SIMULATED OUTBOUND] Configuration for recalibration sent to Messaging System.")
            
            recalibration_filepath = os.path.join(data_folder, "reports", f"recalibration_payload_{batch_id}.json")
            with open(recalibration_filepath, "w", encoding="utf-8") as f:
                json.dump(recalibration_config, f, indent=4)
                
            print(f"➜ Recalibration JSON generated at: {recalibration_filepath}")
            print("----------------------------------------")

        # UNLOCK THE SYSTEM to receive the next batch
        self.waiting_for_human = False
        self.current_pending_batch = None
        print(f"\n[SYSTEM RESUMED] Returning to monitor buffer for the next batch...\n")
        
        return True
        
    def start_server(self):
        trg_ip_listen_on = self.ip_config["ipv4_address"]
        trg_port_listen_on = self.ip_config["port"]
        logging.info("Start server for receiving football player evaluations")
        self.server = ServerREST()
        
        # DOOR 1: INGESTION SYSTEM URL
        self.server.api.add_resource(
            ReceiveJsonApi, "/evaluation/expert-labels",
            endpoint="expert_labels_api",
            resource_class_kwargs={
                'json_schema_path': LABEL_PATH_SCHEMA_REL, 
                'handler': self.handle_expert_message
            }
        )
        
        # DOOR 2: CLASSIFICATION SYSTEM URL
        self.server.api.add_resource(
            ReceiveJsonApi, "/evaluation/classifier-labels",
            endpoint="classifier_labels_api",
            resource_class_kwargs={
                'json_schema_path': LABEL_PATH_SCHEMA_REL, 
                'handler': self.handle_classifier_message
            }
        )
        
        # HUMAN DECISION URL
        self.server.api.add_resource(
            HumanDecisionApi, "/evaluation/decision",
            endpoint="human_decision_api",
            resource_class_kwargs={'handler': self.handle_human_decision_payload}
        )
        
        self.server.run(debug=False, host=trg_ip_listen_on, port=trg_port_listen_on)

    def run(self):
        self.load_config()
        self.load_ip_config()
        self.create_tables()
        print(f"Starting REST server... Listening on {self.ip_config['ipv4_address']}:{self.ip_config['port']}")
        self.start_server()