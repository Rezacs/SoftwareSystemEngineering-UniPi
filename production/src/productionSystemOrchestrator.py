import json
from datetime import datetime, timezone

from src.classifierController import ClassifierController
from src.evaluationSender import EvaluationSender
from src.config import LATEST_SESSION_PATH, LATEST_LABEL_PATH, LOG_PATH


class ProductionSystemOrchestrator:
    def __init__(self):
        self.classifier_controller = ClassifierController()
        self.evaluation_sender = EvaluationSender()


    def _log_event(self, process_name: str, decision_text: str, output_text: str = None):
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        log_entry = {
        "timestamp": timestamp,
        "process": process_name,
        "decision": decision_text
        }

        try:
            if LOG_PATH.exists():
                with open(LOG_PATH, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            else:
                logs = {}
        except Exception:
            logs = {}

        if timestamp not in logs:
            logs[timestamp] = []

        logs[timestamp].append(log_entry)

        if output_text is not None:
            logs[timestamp].append({
            "output": output_text
        })

        with open(LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=4)

    def handle_classifier_received(self, uploaded_file):
        metadata = self.classifier_controller.save_uploaded_classifier(uploaded_file)
        deployment_info = self.classifier_controller.deploy_classifier(
        metadata["classifier_id"],
        metadata["model_filename"]
        )
        self._log_event(
            process_name="Deploy Classifier",
            decision_text=f"approved classifier: {deployment_info['classifier_id']}"
        )
        return deployment_info

    def handle_session_received(self, session: dict):
        with open(LATEST_SESSION_PATH, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=4)
        classification_result = self.classifier_controller.classify(session)
        with open(LATEST_LABEL_PATH, "w", encoding="utf-8") as f:
            json.dump(classification_result, f, indent=4)
        self._log_event(
            process_name="Classify Session",
            decision_text=f"predicted rating: {classification_result['label']} for player {classification_result['player_id']}"
        )
        return classification_result

    def process_classification_result(self, classification_result: dict, communication_controller):
        client_response     = communication_controller.send_label_to_client(classification_result)
        evaluation_response = self.evaluation_sender.send_label_to_evaluation(classification_result)
        delivery_info = {
            "client":     client_response,
            "evaluation": evaluation_response
        }
        self._log_event(
        process_name="Send Label",
        decision_text=f"client={client_response['status']}, evaluation={evaluation_response['status']}",
        output_text="production report"
        )
        return delivery_info