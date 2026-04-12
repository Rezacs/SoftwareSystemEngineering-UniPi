import json
from pathlib import Path
import sys

class PreparationSystemConfiguration:
    """
    Class to handle the configuration parameters of the ingestion system

    Attribututes:
        phase (int) : To set in which phase the system should work, 0 development , 1 evaluation
        classification_system_port (int)
        classification_system_ip (string)
        segregation_system_port (int)
        segregation_system_ip (string)

    """

    def __init__(self,config_file_path):
        """
        Load the parameters from a configuration file
        """
        try:
            config_file_path = Path(config_file_path)
            
            with config_file_path.open(encoding="utf-8") as f:

                config = json.load(f) 
 
                self.phase = config.get("phase",0)

                if self.phase not in [0,1]:
                    print("ERROR> Phase value in configuration file not valid")
                    sys.exit(2)

                self.hosting_ip = config.get("hosting_ip","127.0.0.1")
                self.hosting_port = config.get("hosting_port","5001")

                self.json_schema_path = config.get("json_schema_path")

                if self.json_schema_path is None:
                    print("ERROR> json schema path field is missing in config file")
                    sys.exit(2)

                self.segregation_system_port = config.get("segregation_system_port")
                self.segregation_system_ip =  config.get("segregation_system_ip")
                self.segregation_system_endpoint = config.get("segregation_system_endpoint")
                self.classification_system_port = config.get("classification_system_port")
                self.classification_system_ip = config.get("classification_system_ip")
                self.classification_system_endpoint = config.get("classification_system_endpoint")

        except FileNotFoundError:
            print("ERROR> Configuration file not found")
        except json.JSONDecodeError:
            print("ERROR> Error decoding JSON file")