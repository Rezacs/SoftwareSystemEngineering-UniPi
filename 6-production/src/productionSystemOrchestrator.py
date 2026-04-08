import json
from datetime import datetime

from src.classifierController import ClassifierController
from src.evaluationSender import EvaluationSender
from src.config import LATEST_SESSION_PATH, LATEST_LABEL_PATH, LOG_PATH


class ProductionSystemOrchestrator:
    def __init__(self):
        self.classifier_controller = ClassifierController()
        self.evaluation_sender = EvaluationSender()

    def handle_classifier_received(self, uploaded_file):
        metadata = self.classifier_controller.save_uploaded_classifier(uploaded_file)

        deployment_info = self.classifier_controller.deploy_classifier(
            metadata["classifier_id"],
            metadata["model_filename"]
        )

        self._log_event("classifier_deployed", deployment_info)
        return deployment_info

    def handle_session_received(self, session: dict):
        with open(LATEST_SESSION_PATH, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=4)

        classification_result = self.classifier_controller.classify(session)

        with open(LATEST_LABEL_PATH, "w", encoding="utf-8") as f:
            json.dump(classification_result, f, indent=4)

        self._log_event("session_classified", classification_result)
        return classification_result

    def process_classification_result(self, classification_result: dict, communication_controller):
        client_response = communication_controller.send_label_to_client(classification_result)
        evaluation_response = self.evaluation_sender.send_label_to_evaluation(classification_result)

        self._log_event("label_sent", {
            "client": client_response,
            "evaluation": evaluation_response
        })

        return {
            "client": client_response,
            "evaluation": evaluation_response
        }

    def _log_event(self, event_type: str, data: dict):
        log_entry = {
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        try:
            if LOG_PATH.exists():
                with open(LOG_PATH, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            else:
                logs = []
        except Exception:
            logs = []

        logs.append(log_entry)

        with open(LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=4)