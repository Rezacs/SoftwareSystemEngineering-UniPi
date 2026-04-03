import json

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
            
            with open(config_file_path) as f:

                config = json.load(f) 
 
                self.phase = config["phase"]
                self.hosting_ip = config["hosting_ip"]
                self.hosting_port = config["hosting_port"]
                self.classification_system_port = config["classification_system_port"]
                self.classification_system_ip =  config["classification_system_ip"]
                self.segregation_system_port = config["segregation_system_port"]
                self.segregation_system_ip = config["segregation_system_ip"]

        except FileNotFoundError:
            print("ERROR> Configuration file not found")
        except json.JSONDecodeError:
            print("ERROR> Error decoding JSON file")