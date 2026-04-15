import json
import sys
from pathlib import Path


class PreparationSystemConfiguration:
    """Handles the configuration parameters for the data preparation system.

    This class loads configuration settings from a JSON file, validates the
    types and values of the required parameters, and makes them available
    as instance attributes. If any parameter is missing, invalid, or if the file
    cannot be read, the application will exit with a specific error code.

    Attributes:
        phase (int): The operating phase of the system (0 for development, 1 for evaluation).
        hosting_ip (str): The IP address where the preparation system is hosted.
        hosting_port (int): The port number where the preparation system listens.
        json_schema_path (str): The file path to the expected JSON validation schema.
        number_of_threads (int): The maximum number of worker threads allowed (must be 1-4).
        segregation_system_port (int): The port of the downstream segregation system.
        segregation_system_ip (str): The IP address of the downstream segregation system.
        segregation_system_endpoint (str): The API endpoint route for the segregation system.
        classification_system_port (int): The port of the downstream classification system.
        classification_system_ip (str): The IP address of the downstream classification system.
        classification_system_endpoint (str): The API endpoint route for the classification system.
    """

    def __init__(self, config_file_path):
        """Loads and validates system parameters from the given configuration file.

        Args:
            config_file_path (str or Path): The path to the JSON configuration file.

        Raises:
            SystemExit: Terminates the program with specific status codes if the
                file is missing (100), contains invalid JSON (101), or if any
                configuration values fail validation checks (1-9).
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