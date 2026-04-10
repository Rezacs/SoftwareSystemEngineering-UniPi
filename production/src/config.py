import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "productionConfig.json"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


CONFIG = load_config()

PRODUCTION_HOST = CONFIG["production_system"]["host"]
PRODUCTION_PORT = CONFIG["production_system"]["port"]

CLASSIFIER_RECEIVED_ENDPOINT = CONFIG["endpoints"]["classifier_received"]
PREPARED_SESSION_RECEIVED_ENDPOINT = CONFIG["endpoints"]["prepared_session_received"]
STATUS_ENDPOINT = CONFIG["endpoints"]["status"]

CLIENT_SIDE_HOST = CONFIG["client_side_system"]["host"]
CLIENT_SIDE_PORT = CONFIG["client_side_system"]["port"]
CLIENT_SIDE_LABEL_ENDPOINT = CONFIG["client_side_system"]["label_endpoint"]
CLIENT_SIDE_LABEL_URL = (
    f"http://{CLIENT_SIDE_HOST}:{CLIENT_SIDE_PORT}{CLIENT_SIDE_LABEL_ENDPOINT}"
)

EVALUATION_HOST = CONFIG["evaluation_system"]["host"]
EVALUATION_PORT = CONFIG["evaluation_system"]["port"]
EVALUATION_CLASSIFIER_LABEL_ENDPOINT = CONFIG["evaluation_system"]["classifier_label_endpoint"]
EVALUATION_CLASSIFIER_LABEL_URL = (
    f"http://{EVALUATION_HOST}:{EVALUATION_PORT}{EVALUATION_CLASSIFIER_LABEL_ENDPOINT}"
)

MESSAGING_HOST = CONFIG["messaging_system"]["host"]
MESSAGING_PORT = CONFIG["messaging_system"]["port"]
MESSAGING_CONFIGURATION_ENDPOINT = CONFIG["messaging_system"]["configuration_endpoint"]
MESSAGING_CONFIGURATION_URL = (
    f"http://{MESSAGING_HOST}:{MESSAGING_PORT}{MESSAGING_CONFIGURATION_ENDPOINT}"
)

CLASSIFIERS_DIR = BASE_DIR / CONFIG["paths"]["classifiers_dir"]
LATEST_CLASSIFIER_PATH = BASE_DIR / CONFIG["paths"]["latest_classifier"]
LATEST_SESSION_PATH = BASE_DIR / CONFIG["paths"]["latest_session"]
STATUS_PATH = BASE_DIR / CONFIG["paths"]["status"]
LATEST_LABEL_PATH = BASE_DIR / CONFIG["paths"]["latest_label"]
EVALUATION_PAYLOAD_PATH = BASE_DIR / CONFIG["paths"]["evaluation_payload"]
LOG_PATH = PROJECT_ROOT / "logs" / "productionLog.json"

FEATURE_COLUMNS = CONFIG["classification"]["feature_columns"]
EVALUATION_ENABLED = CONFIG["evaluation"]["enabled"]


def ensure_directories():
    CLASSIFIERS_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_CLASSIFIER_PATH.parent.mkdir(parents=True, exist_ok=True)
    LATEST_SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    LATEST_LABEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVALUATION_PAYLOAD_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)