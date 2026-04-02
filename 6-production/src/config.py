import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "Data" / "configs" / "config.json"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


CONFIG = load_config()

# Production System
PRODUCTION_HOST = CONFIG["production_system"]["host"]
PRODUCTION_PORT = CONFIG["production_system"]["port"]

# Inbound endpoints
CLASSIFIER_RECEIVED_ENDPOINT = CONFIG["endpoints"]["classifier_received"]
PREPARED_SESSION_RECEIVED_ENDPOINT = CONFIG["endpoints"]["prepared_session_received"]

# Client-side System
CLIENT_SIDE_HOST = CONFIG["client_side_system"]["host"]
CLIENT_SIDE_PORT = CONFIG["client_side_system"]["port"]
CLIENT_SIDE_LABEL_ENDPOINT = CONFIG["client_side_system"]["label_endpoint"]
CLIENT_SIDE_LABEL_URL = (
    f"http://{CLIENT_SIDE_HOST}:{CLIENT_SIDE_PORT}{CLIENT_SIDE_LABEL_ENDPOINT}"
)

# Evaluation System
EVALUATION_HOST = CONFIG["evaluation_system"]["host"]
EVALUATION_PORT = CONFIG["evaluation_system"]["port"]
EVALUATION_LABEL_ENDPOINT = CONFIG["evaluation_system"]["label_endpoint"]
EVALUATION_LABEL_URL = (
    f"http://{EVALUATION_HOST}:{EVALUATION_PORT}{EVALUATION_LABEL_ENDPOINT}"
)

# Messaging System
MESSAGING_HOST = CONFIG["messaging_system"]["host"]
MESSAGING_PORT = CONFIG["messaging_system"]["port"]
MESSAGING_CONFIGURATION_ENDPOINT = CONFIG["messaging_system"]["configuration_endpoint"]
MESSAGING_CONFIGURATION_URL = (
    f"http://{MESSAGING_HOST}:{MESSAGING_PORT}{MESSAGING_CONFIGURATION_ENDPOINT}"
)

# Paths
CLASSIFIERS_DIR = BASE_DIR / CONFIG["paths"]["classifiers_dir"]
LATEST_CLASSIFIER_PATH = BASE_DIR / CONFIG["paths"]["latest_classifier"]
LATEST_SESSION_PATH = BASE_DIR / CONFIG["paths"]["latest_session"]
STATUS_PATH = BASE_DIR / CONFIG["paths"]["status"]
LATEST_LABEL_PATH = BASE_DIR / CONFIG["paths"]["latest_label"]
EVALUATION_PAYLOAD_PATH = BASE_DIR / CONFIG["paths"]["evaluation_payload"]
LOG_PATH = BASE_DIR / CONFIG["paths"]["log"]

# Classification
FEATURE_COLUMNS = CONFIG["classification"]["feature_columns"]

# Evaluation Phase
EVALUATION_ENABLED = CONFIG["evaluation"]["enabled"]


def ensure_directories():
    CLASSIFIERS_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_CLASSIFIER_PATH.parent.mkdir(parents=True, exist_ok=True)
    LATEST_SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    LATEST_LABEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVALUATION_PAYLOAD_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)