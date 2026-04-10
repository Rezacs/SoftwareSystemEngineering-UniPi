from preparation.raw_session_receiver import RawSessionReceiver
from preparation.prepared_session_creator import PreparedSessionCreator
from preparation.preparation_system_config import PreparationSystemConfiguration
from pathlib import Path

from flask import Flask, request, jsonify

import requests
import json
import datetime


class PreparationSystemOrchestrator:
    """
    Orchestrator for the preparation system, receive the raw sessions, process them, and creates
    the prepared session, then it sends them to segregation system or classification system, depending
    in which phase is running.

    Args:
        config_file_path (str): the configuration file in which are specified all the parameters to run
                                the system.
    """

    def __init__(self,config_file_path : str = None,testing_mode : bool = False):

        if config_file_path is None:
            config_file_path = Path(__file__).resolve().parents[1] / "config" / "preparationConfig.json"

        self.testing_mode=testing_mode

        if self.testing_mode:

            self.log_file_path=Path(__file__).resolve().parents[1] / "logs" / "PreparationLog.json"

            with open (self.log_file_path,'r') as tmp_log:
                
                self.log=json.load(tmp_log)
        
        print(f"[INFO] Preparation system orchestrator initialization...")

        self.preparation_system_config = PreparationSystemConfiguration(config_file_path)

        print(f"""
               --- Preparation System Configuration ---
               Phase:             {self.preparation_system_config.phase}
               Classification System: {self.preparation_system_config.classification_system_ip}:{self.preparation_system_config.classification_system_port}
               Segregation System: {self.preparation_system_config.segregation_system_ip}:{self.preparation_system_config.segregation_system_port}
               Testing mode: {self.testing_mode}
               --------------------------------------
        """)

        self.raw_session_receiver = RawSessionReceiver()

        print(f"[INFO] Raw session receiver initialized")

        self.prepared_session_creator = PreparedSessionCreator()

        print(f"[INFO] Prepared session creator initialized")

        self.app = Flask(__name__)

        self.app.add_url_rule('/run', methods=['POST'], view_func=self.run)

        print(f"[INFO] Flask service started initialized")


    def run(self):

        #Receive raw session
        raw_session = self.raw_session_receiver.receive_raw_session()

        if raw_session == None:

            return jsonify({"Message": "Raw session received has an invalid schema"}), 400

        #Create prepared session
        raw_session = self.prepared_session_creator.parse_raw_session(raw_session)

        #Correct missing samples
        raw_session = self.prepared_session_creator.correct_missing_samples(raw_session)

        #Correct outliers
        raw_session = self.prepared_session_creator.correct_absolute_outliers(raw_session)

        #Extract features
        batch_prepared_session=self.prepared_session_creator.extract_features(raw_session)

        #LOGIC TO DECOMPOSE THE BATCH
        features=batch_prepared_session.get("features")
        prepared_sessions=[]
        for d in features:
            prepared_session={
                "session_id" : batch_prepared_session.get("UUID"),
                "player_id" : d.get("player_id"),
                "skill_overall" : d.get("skillOverall"),
                "social_influence_score" : d.get("social_influence_score"),
                "injuries_impact_score" : d.get("injuries_impact_score"),
                "label" : d.get("label")
            }
            prepared_sessions.append(prepared_session)
        
        if self.testing_mode:
            log=[]

        if self.preparation_system_config.phase==0:

            for p in prepared_sessions:
                #Development phase
                #Send to segregation system
                url = f"http://{self.preparation_system_config.segregation_system_ip}:{self.preparation_system_config.segregation_system_port}/prepared-sessions"
                risp = requests.post(url, json=p)
                print(risp)
                if self.testing_mode:
                    last_timestamp=datetime.datetime.now().isoformat()
                    last_action={
                        "timestamp" : last_timestamp,
                        "phase" : 0,
                        "action" : "prepared session sent to segregation system"
                    }
                    log.append(last_action)
            
            #update the log file
            if self.testing_mode:

                self.log[f"{last_timestamp}"]=log

                with open(self.log_file_path, 'w') as file:

                    json.dump(self.log, file, indent=4)

            return jsonify({"Message": "Prepared session correctly sent to segregation system"}), 200

        for p in prepared_sessions:
            #Evaluation phase send to classification system
            url = f"http://{self.preparation_system_config.classification_system_ip}:{self.preparation_system_config.classification_system_port}/session"
            risp = requests.post(url, json=p)
            print(risp)
            if self.testing_mode:
                last_timestamp=datetime.datetime.now().isoformat()
                last_action={
                        "timestamp" : last_timestamp,
                        "phase" : self.preparation_system_config.phase,
                        "action" : "prepared session sent to classification system"
                }
                log.append(last_action)

        if self.testing_mode:

            self.log[f"{last_timestamp}"]=log

            with open(self.log_file_path, 'w') as file:

                json.dump(self.log, file, indent=4)

        return jsonify({"Message": "Prepared session correctly sent to classification system"}), 200

        
    
    def start(self):
        """
        Start Flask server

        """

        print("Starting Flask server...")

        self.app.run(host=self.preparation_system_config.hosting_ip, port=self.preparation_system_config.hosting_port)