from common.json_io import JsonIO
from ingestion.record_receiver import RecordReceiver
from ingestion.raw_session_creator import RawSessionCreator
from ingestion.ingestion_system_config import IngestionSystemConfiguration
from ingestion.records_buffer import RecordsBuffer
import numpy as np
import pandas as pd
import requests
from flask import Flask, request, jsonify


class IngestionSystemOrchestrator:

    def __init__(self,config_file_path = "config/ingestionConfig.json"):

        print(f"[INFO] Ingestion system orchestrator initialization...")

        

        self.ingestion_system_config = IngestionSystemConfiguration(config_file_path)

        self.receiver = RecordReceiver()

        print(f"[INFO] Record receiver initialized")

        self.raw_session_creator = RawSessionCreator(self.ingestion_system_config.sufficient_record_treshold)

        print(f"[INFO] Raw session creator initialized")

        self.records_buffer = RecordsBuffer("fscDB.db")

        if self.records_buffer.init_db():
            print(f"[INFO] Database correctly initialized")
        else:
            print("[ERROR] Error encountered initializing the database")
            exit(1)


        self.app = Flask(__name__)

        self.app.add_url_rule('/run', methods=['POST'], view_func=self.run)

        print(f"[INFO] Flask service started initialized")

        print(f"""
               --- Ingestion System Configuration ---
               Phase:             {self.ingestion_system_config.phase}
               Thresholds:        Missing_Samples: {self.ingestion_system_config.missing_samples_treshold}, Sufficient_Records: {self.ingestion_system_config.sufficient_record_treshold}
               Evaluation System: {self.ingestion_system_config.evaluation_system_ip}:{self.ingestion_system_config.evaluation_system_port}
               Preparation System: {self.ingestion_system_config.preparation_system_ip}:{self.ingestion_system_config.preparation_system_port}
               --------------------------------------
        """)


    def run(self,input_path="data/outputs/client_message.json",output_path="data/outputs/raw_session.json"):

        record , table = self.receiver.receive_record()

        if record is None:
            return jsonify({"Error": "Bad data"}), 400

        record = pd.DataFrame(record, index=[0]).reset_index(drop=True)

        if self.records_buffer.upsert_with_dataframe(record):
            print(f"[INFO] Record inserted in the Buffer")
        else:
            print(f"[ERROR] Error occurred inserting the record in the buffer")

        #Check if it is possible to create a raw session

        n_rows=self.records_buffer.getNumberOfAvailableRecords()

        if not self.raw_session_creator.isNumberOfRecordsSufficient(n_rows):
            return jsonify({"Message": "Data correctly received"}), 200

        #create raw session

        records,ids=self.records_buffer.retrieve_last_records(n_rows)

        raw_session = self.raw_session_creator.create_raw_session(records)

        #mark missing samples and check if raw session is valid

        if self.raw_session_creator.mark_missing_samples(raw_session) > self.ingestion_system_config.missing_samples_treshold:
            return jsonify({"Message" : "Received data are incomplete"}),200

        #check if is evaluation phase
        if self.ingestion_system_config.phase==1:
            #send label to evaluation system
            records = raw_session["records"]
            for record in records:
                #labels.append({"playerID" : record["playerID"], "source" : "expert", "rating" : record["rating"]})
                #json={"UUID": raw_session["UUID"] , "created_at" : raw_session["created_at"], "labels" : labels}
                json={"playerID" : record["player_id"], "source" : "expert", "label" : record["label"]}
                url = f"http://{self.ingestion_system_config.evaluation_system_ip}:{self.ingestion_system_config.evaluation_system_port}"
                risp = requests.post(url, json=json)
                print(risp)
                #pass
                

        
        #send data preparation system
        url = f"http://{self.ingestion_system_config.preparation_system_ip}:{self.ingestion_system_config.evaluation_system_port}"
        risp = requests.post(url, json=raw_session)
        print(risp)

        if not self.records_buffer.delete_records(ids):
            return jsonify({"Message":"Error occured extracting records from buffer"}),500

        return jsonify({"Message":"Raw session correctly sent to preparation system"}),200



        
    
    def start(self): # todo 127.0.0.1   192.168.97.85
        """
        Start Flask server

        """

        print("[INFO] Starting Flask server...")

        self.app.run(host=self.ingestion_system_config.hosting_ip, port=self.ingestion_system_config.hosting_port)
    