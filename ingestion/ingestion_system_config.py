import json
from pathlib import Path
import sys

class IngestionSystemConfiguration:
    """
    Class to handle the configuration parameters of the ingestion system

    Attribututes:
        phase (int) : To set in which phase the system should work, 0 development , 1 evaluation
        missing_samples_treshold (int) : treshold to specify how much missing samples must be present to discard a sesssion
        sufficient_record_treshold (int): specify the minimum records a raw session must have
        json_schema_path : path to the json schema to validate the records received in input
        evaluation_system_port (int)
        evaluation_system_ip (string)
        evalutation_system_endpoint (string) 
        preparation_system_port (int)
        preparation_system_ip (string)
        preparation_system_endpoint (string)

    """

    def __init__(self,config_file_path):
        """
        Load the parameters from a configuration file
        """
        try:
            config_file_path = Path(config_file_path)
            
            with config_file_path.open(encoding="utf-8") as f:

                config = json.load(f) 

                self.hosting_ip = config.get("hosting_ip","127.0.0.1")
                self.hosting_port = config.get("hosting_port","5001")

                self.phase = config.get("phase",0)

                if self.phase not in [0,1]:
                    print("ERROR> Phase value in configuration file not valid")
                    sys.exit(2)

                self.missing_samples_treshold = config.get("missing_samples_treshold",20)
                self.sufficient_record_treshold = config.get("sufficient_records_treshold",10)

                self.json_schema_path = config.get("json_schema_path")

                if self.json_schema_path is None:
                    print("ERROR> json schema path field is missing in config file")
                    sys.exit(2)

                self.evaluation_system_port = config.get("evaluation_system_port")
                self.evaluation_system_ip =  config.get("evaluation_system_ip")
                self.evaluation_system_endpoint = config.get("evaluation_system_endpoint")
                self.preparation_system_port = config.get("preparation_system_port")
                self.preparation_system_ip = config.get("preparation_system_ip")
                self.preparation_system_endpoint = config.get("preparation_system_endpoint")

                
        except FileNotFoundError:
            print("ERROR> Configuration file not found")
        except json.JSONDecodeError:
            print("ERROR> Error decoding JSON file")