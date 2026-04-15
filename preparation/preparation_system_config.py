import json
import sys
from pathlib import Path


class PreparationSystemConfiguration:
    """
    Class to handle the configuration parameters of the ingestion system

    Attributes:
        phase (int) : To set in which phase the system should work, 0 development , 1 evaluation
        classification_system_port (int)
        classification_system_ip (string)
        segregation_system_port (int)
        segregation_system_ip (string)

    """

    def __init__(self, config_file_path):
        """
        Load the parameters from a configuration file
        """
        try:
            config_file_path = Path(config_file_path)

            with config_file_path.open(encoding="utf-8") as f:

                config = json.load(f)

                self.phase = config.get("phase", 0)

                if self.phase not in [0, 1]:
                    print("ERROR> Phase value in configuration file not valid")
                    sys.exit(2)

                self.hosting_ip = config.get("hosting_ip", "127.0.0.1")

                if not isinstance(self.hosting_ip, str):
                    print("ERROR> hosting_ip in configuration file not valid")
                    sys.exit(1)

                self.hosting_port = config.get("hosting_port", "5001")

                if not isinstance(self.hosting_port, int):
                    print("ERROR> hosting_port in configuration file not valid")
                    sys.exit(1)

                self.json_schema_path = config.get("json_schema_path")

                if not isinstance(self.json_schema_path, str):
                    print("ERROR> json_schema_path field is missing/invalid in config file")
                    sys.exit(2)

                self.number_of_threads = config.get("number_of_threads", 3)

                if not isinstance(self.number_of_threads, int) and self.number_of_threads not in range(1, 5):
                    print("ERROR> MAX num of threads in configuration file not valid , acceptable [1 to 5]")
                    sys.exit(3)

                self.segregation_system_port = config.get("segregation_system_port")

                if not isinstance(self.segregation_system_port, int):
                    print("ERROR> segregation_system_port field is missing/invalid in config file")
                    sys.exit(4)

                self.segregation_system_ip = config.get("segregation_system_ip")

                if not isinstance(self.segregation_system_ip, str):
                    print("ERROR> segregation_system_ip field is missing/invalid in config file")
                    sys.exit(5)

                self.segregation_system_endpoint = config.get("segregation_system_endpoint")

                if not isinstance(self.segregation_system_endpoint, str):
                    print("ERROR> segregation_system_endpoint field is missing/invalid in config file")
                    sys.exit(6)

                self.classification_system_port = config.get("classification_system_port")

                if not isinstance(self.classification_system_port, int):
                    print("ERROR> classification_system_port field is missing/invalid in config file")
                    sys.exit(7)

                self.classification_system_ip = config.get("classification_system_ip")

                if not isinstance(self.classification_system_ip, str):
                    print("ERROR> classification_system_ip field is missing/invalid in config file")
                    sys.exit(8)

                self.classification_system_endpoint = config.get("classification_system_endpoint")

                if not isinstance(self.classification_system_endpoint, str):
                    print("ERROR> classification_system_endpoint field is missing/invalid in config file")
                    sys.exit(9)

        except FileNotFoundError:
            print("ERROR> Configuration file not found")
            sys.exit(100)
        except json.JSONDecodeError:
            print("ERROR> Error decoding JSON file")
            sys.exit(101)
