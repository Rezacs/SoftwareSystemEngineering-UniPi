import json

import requests
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "productionConfig.json"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


_cfg = load_config()

EVALUATION_ENABLED              = _cfg["evaluation"]["enabled"]
EVALUATION_CLASSIFIER_LABEL_URL = (
    f"http://{_cfg['evaluation_system']['host']}:"
    f"{_cfg['evaluation_system']['port']}"
    f"{_cfg['evaluation_system']['classifier_label_endpoint']}"
)
EVALUATION_PAYLOAD_PATH = Path(_cfg["paths"]["evaluation_payload"])

class EvaluationSender:
    def __init__(self):
        self.evaluation_enabled = EVALUATION_ENABLED

    def is_evaluation_phase(self):
        return self.evaluation_enabled

    def build_payload(self, classification_result: dict):
        payload = {
            "player_id": classification_result["player_id"],
            #"source": "classifier",
            "label": classification_result["label"],
            "classifier_id": classification_result["classifier_id"]
        }

        with open(EVALUATION_PAYLOAD_PATH, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=4)

        return payload

    def send_label_to_evaluation(self, classification_result: dict):
        if not self.is_evaluation_phase():
            print("[EvaluationSender] Evaluation skipped.")
            return {"status": "evaluation_skipped"}

        payload = self.build_payload(classification_result)
        print(f"[EvaluationSender] Sending label to Evaluation: {payload}")

        try:
            print(f"[EvaluationSender] Sending label to Evaluation at {EVALUATION_CLASSIFIER_LABEL_URL} ...")
            response = requests.post(EVALUATION_CLASSIFIER_LABEL_URL, json=payload, timeout=10)
            print(f"[EvaluationSender] Label sent to Evaluation ({response.status_code})")
            return {
                "status": "sent",
                "evaluation_response_code": response.status_code
            }
        except Exception as e:
            print(f"[EvaluationSender] Failed to send label to Evaluation: {e}")
            return {
                "status": "error",
                "message": str(e)
            }