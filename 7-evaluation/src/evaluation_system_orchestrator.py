"""
    Evaluation System Orchestrator : loads all configs and runs the listening server
"""
import json
import logging
import threading
import os

from src.utility.json_validation import validate_json_data_file
from src.utility import data_folder
from src.comms import ServerREST
from src.comms.json_transfer_api import ReceiveJsonApi
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

    def __init__(self):
        self.player_store_controller = PlayerStoreController()
        self.evaluation_report_controller = EvaluationReportController()
        self.config = None
        self.ip_config = None
        self.server = None

    def load_config(self):
        """Loads and validates evaluation system configuration file"""
        config_path = os.path.join(data_folder, CONFIG_PATH_REL)
        with open(config_path, "r", encoding="UTF-8") as file:
            self.config = json.load(file)
            
        if not validate_json_data_file(self.config, CONFIG_SCHEMA_PATH_REL):
            logging.error("Invalid evaluation config file.")
            raise ValueError("Evaluation config validation failed.")

    def load_ip_config(self):
        """Loads and validates the IP and Port configuration"""
        ip_path = os.path.join(data_folder, IP_PATH_REL)
        with open(ip_path, "r", encoding="UTF-8") as file:
            self.ip_config = json.load(file)
            
        if not validate_json_data_file(self.ip_config, IP_PATH_SCHEMA_REL):
            logging.error("Invalid IP config file.")
            raise ValueError("IP config validation failed.")

    def create_tables(self):
        """Creates LOCAL sqlite3 db tables for expert and classifier labels"""
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
                source TEXT
            )
        """
        self.player_store_controller.store.ps_create_table(query_expert)
        self.player_store_controller.store.ps_create_table(query_classifier)

    # def handle_message(self, label_dict):
    #     """
    #     Callback function passed to the comms API. 
    #     Executes the saving logic in a separate thread.
    #     This handles data from BOTH the test client and the real Classifier.
    #     """
    #     print(f"Orchestrator received data for processing: {label_dict.get('player_id')}")
        
    #     # We launch a thread so the HTTP response is sent back immediately 
    #     # while the database does the heavy lifting in the background.
    #     thread = threading.Thread(
    #         target=self.player_store_controller.save_label_prompt_eval,
    #         args=(label_dict, self.config)
    #     )
    #     thread.start()
    #     return True

    def handle_message(self, label_dict):
        """
        Processes incoming labels and triggers a human-readable report.
        """
        player_id = label_dict.get('player_id')
        source = label_dict.get('source')
        
        print(f"Orchestrator processing {source} data for: {player_id}")
        
        # 1. Save data directly (Blocking call ensures data is in DB before report starts)
        self.player_store_controller.save_label_prompt_eval(label_dict, self.config)
        
        # 2. Trigger the Report
        # We generate the report specifically when an 'expert' rating arrives 
        # to complete the comparison for the Human Manager.
        if source == 'expert':
            self.evaluation_report_controller.generate_human_report(player_id)
            
        return True

    def start_server(self):
        """Starts the REST server at the given IPv4 and Port, and assigns handler"""
        trg_ip_listen_on = self.ip_config["ipv4_address"]
        trg_port_listen_on = self.ip_config["port"]
        
        logging.info("Start server for receiving football player evaluations")
        
        # 1. Initialize the Server Base
        self.server = ServerREST()
        
        # 2. Add the Resource (Endpoint)
        # Note: Mapping to '/evaluation' to match your test_client.py
        self.server.api.add_resource(
            ReceiveJsonApi,
            "/evaluation",
            resource_class_kwargs={
                'json_schema_path': LABEL_PATH_SCHEMA_REL,
                'handler': self.handle_message
            }
        )
        
        # 3. Run the Flask loop
        self.server.run(debug=False, host=trg_ip_listen_on, port=trg_port_listen_on)

    def run(self):
        """Orchestrator loads config, prepares DB, and starts REST server"""
        self.load_config()
        print("Threshold values loaded from eval_config file.")
        
        self.load_ip_config()
        print(f"Target IPv4 ({self.ip_config['ipv4_address']}) and port ({self.ip_config['port']}) loaded.")
        
        self.create_tables()
        print("SQLite Database and tables created/verified.")
        
        print(f"Starting REST server... Listening on {self.ip_config['ipv4_address']}:{self.ip_config['port']}/evaluation")
        self.start_server()