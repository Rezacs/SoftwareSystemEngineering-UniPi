import json

class IngestionSystemConfiguration:
    """
    Class to handle the configuration parameters of the ingestion system

    Attribututes:
        phase (int) : To set in which phase the system should work, 0 development , 1 evaluation
        missing_samples_treshold (int) : treshold to specify how much missing samples must be present to discard a sesssion
        sufficient_record_treshold (int): specify the minimum records a raw session must have
        evaluation_system_port (int)
        evaluation_system_ip (string)
        preparation_system_port (int)
        preparation_system_ip (string)

    """

    def __init__(self,config_file_path):
        """
        Load the parameters from a configuration file
        """
        try:
            
            with open(config_file_path) as f:

                config = json.load(f) 

                self.hosting_ip = config["hosting_ip"]
                self.hosting_port = config["hosting_port"]
                self.phase = config["phase"]
                self.missing_samples_treshold = config["missing_samples_treshold"]
                self.sufficient_record_treshold = config["sufficient_records_treshold"]

                self.evaluation_system_port = config["evaluation_system_port"]
                self.evaluation_system_ip =  config["evaluation_system_ip"]
                self.preparation_system_port = config["preparation_system_port"]
                self.preparation_system_ip = config["preparation_system_ip"]

                
        except FileNotFoundError:
            print("ERROR> Configuration file not found")
        except json.JSONDecodeError:
            print("ERROR> Error decoding JSON file")