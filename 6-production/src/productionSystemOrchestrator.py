import json
from datetime import datetime

from src.classifierController import ClassifierController
from src.evaluationSender import EvaluationSender
from src.config import (
    LATEST_SESSION_PATH,
    LATEST_LABEL_PATH,
    LOG_PATH
)


class ProductionSystemOrchestrator:
    def __init__(self):
        self.classifier_controller = ClassifierController()
        self.evaluation_sender = EvaluationSender()

    # =========================
    # BPMN: Classifier Received → Deploy Classifier
    # =========================
    def handle_classifier_received(self, data: dict):
        classifier_id = data["classifier_id"]
        model_filename = data["model_filename"]
        source_model_path = data.get("source_model_path")

        # Save classifier
        self.classifier_controller.save_classifier(
            source_model_path,
            classifier_id,
            model_filename
        )

        # Deploy classifier
        deployment_info = self.classifier_controller.deploy_classifier(
            classifier_id,
            model_filename
        )

        self._log_event("classifier_deployed", deployment_info)

        return deployment_info

    # =========================
    # BPMN: Prepared Session Received → Classify
    # =========================
    def handle_session_received(self, session: dict):
        # Save latest session
        with open(LATEST_SESSION_PATH, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=4)

        # Classify
        classification_result = self.classifier_controller.classify(session)

        # Save label output
        with open(LATEST_LABEL_PATH, "w", encoding="utf-8") as f:
            json.dump(classification_result, f, indent=4)

        self._log_event("session_classified", classification_result)

        return classification_result

    # =========================
    # BPMN: Send Label → Client + Evaluation Phase
    # =========================
    def process_classification_result(self, classification_result: dict, communication_controller):
        # Send to client-side
        client_response = communication_controller.send_label_to_client(classification_result)

        # Evaluation Phase?
        evaluation_response = self.evaluation_sender.send_label_to_evaluation(classification_result)

        self._log_event("label_sent", {
            "client": client_response,
            "evaluation": evaluation_response
        })

        return {
            "client": client_response,
            "evaluation": evaluation_response
        }

    # =========================
    # Logging
    # =========================
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
        except:
            logs = []

        logs.append(log_entry)

        with open(LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=4)