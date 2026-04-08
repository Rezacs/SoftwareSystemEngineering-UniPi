import json

import requests

from src.config import (
    EVALUATION_ENABLED,
    EVALUATION_CLASSIFIER_LABEL_URL,
    EVALUATION_PAYLOAD_PATH
)


class EvaluationSender:
    def __init__(self):
        self.evaluation_enabled = EVALUATION_ENABLED

    def is_evaluation_phase(self):
        return self.evaluation_enabled

    def build_payload(self, classification_result: dict):
        payload = {
            "player_id": classification_result["player_id"],
            "source": "classifier",
            "rating": classification_result["rating"],
            "classifier_id": classification_result["classifier_id"]
        }

        with open(EVALUATION_PAYLOAD_PATH, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=4)

        return payload

    def send_label_to_evaluation(self, classification_result: dict):
        if not self.is_evaluation_phase():
            return {"status": "evaluation_skipped"}

        payload = self.build_payload(classification_result)

        try:
            response = requests.post(EVALUATION_CLASSIFIER_LABEL_URL, json=payload)
            return {
                "status": "sent",
                "evaluation_response_code": response.status_code
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }