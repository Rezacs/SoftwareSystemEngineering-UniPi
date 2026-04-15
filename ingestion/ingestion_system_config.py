import json
import sys
from pathlib import Path


class IngestionSystemConfiguration:
    """
    Class to handle the configuration parameters of the ingestion system

    Attributes:
        phase (int) : To set in which phase the system should work, 0 development , 1 evaluation
        missing_samples_threshold (int) : threshold to specify how much missing samples must be present
                                          to discard a session
        sufficient_record_threshold (int): specify the minimum records a raw session must have
        json_schema_path : path to the json schema to validate the records received in input
        evaluation_system_port (int)
        evaluation_system_ip (string)
        evaluation_system_endpoint (string)
        preparation_system_port (int)
        preparation_system_ip (string)
        preparation_system_endpoint (string)

    """

    def __init__(self, config_file_path):
        """
        Load the parameters from a configuration file
        """
        try:
            config_file_path = Path(config_file_path)

            with config_file_path.open(encoding="utf-8") as f:

                config = json.load(f)

                self.hosting_ip = config.get("hosting_ip", "127.0.0.1")

                if not isinstance(self.hosting_ip, str):
                    print("ERROR> hosting_ip in configuration file not valid")
                    sys.exit(1)

                self.hosting_port = config.get("hosting_port", "5001")

                if not isinstance(self.hosting_port, int):
                    print("ERROR> hosting_port in configuration file not valid")
                    sys.exit(1)

                self.phase = config.get("phase")

                if self.phase not in [0, 1]:
                    print("ERROR> Phase value in configuration file not valid")
                    sys.exit(2)

                self.number_of_threads = config.get("number_of_threads", 3)

                if not isinstance(self.number_of_threads, int) and self.number_of_threads not in range(1, 10):
                    print("ERROR> MAX num of threads in configuration file not valid , acceptable [1 to 10]")
                    sys.exit(3)

                self.missing_samples_threshold = config.get("missing_samples_threshold", 20)

                if not isinstance(self.missing_samples_treshold, int):
                    print("ERROR> Missing samples treshold in configuration file not valid")
                    sys.exit(4)

                self.sufficient_record_threshold = config.get("sufficient_records_threshold", 10)

                if not isinstance(self.sufficient_record_threshold, int):
                    print("ERROR> sufficient record threshold in configuration file not valid")
                    sys.exit(5)

                self.json_schema_path = config.get("json_schema_path")

                if not isinstance(self.json_schema_path, str):
                    print("ERROR> json_schema_path field is missing/invalid in config file")
                    sys.exit(6)

                self.evaluation_system_port = config.get("evaluation_system_port")

                if not isinstance(self.evaluation_system_port, int):
                    print("ERROR> evaluation_system_port field is missing/invalid in config file")
                    sys.exit(7)

                self.evaluation_system_ip = config.get("evaluation_system_ip")

                if not isinstance(self.evaluation_system_ip, str):
                    print("ERROR> evaluation_system_ip field is missing/invalid in config file")
                    sys.exit(8)

                self.evaluation_system_endpoint = config.get("evaluation_system_endpoint")

                if not isinstance(self.evaluation_system_endpoint, str):
                    print("ERROR> evaluation_system_endpoint field is missing/invalid in config file")
                    sys.exit(9)

                self.preparation_system_port = config.get("preparation_system_port")

                if not isinstance(self.preparation_system_port, int):
                    print("ERROR> preparation_system_port field is missing/invalid in config file")
                    sys.exit(10)

                self.preparation_system_ip = config.get("preparation_system_ip")

                if not isinstance(self.preparation_system_ip, str):
                    print("ERROR> preparation_system_ip field is missing/invalid in config file")
                    sys.exit(11)

                self.preparation_system_endpoint = config.get("preparation_system_endpoint")

                if not isinstance(self.preparation_system_endpoint, str):
                    print("ERROR> evaluation_system_endpoint field is missing/invalid in config file")
                    sys.exit(12)

        except FileNotFoundError:
            print("ERROR> Configuration file not found")
            sys.exit(100)
        except json.JSONDecodeError:
            print("ERROR> Error decoding JSON file")
            sys.exit(101)
