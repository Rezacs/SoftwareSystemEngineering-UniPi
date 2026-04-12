import json
import time
from datetime import datetime, timezone

from src.classifierController import ClassifierController
from src.evaluationSender import EvaluationSender
from src.config import LATEST_SESSION_PATH, LATEST_LABEL_PATH, LOG_PATH


class ProductionSystemOrchestrator:
    def __init__(self):
        self.classifier_controller = ClassifierController()
        self.evaluation_sender = EvaluationSender()
        self.tmp_log = []


    def _log_event(self, initial_timestamp: str, process_code: str, latency: float, outcome: str):
        log_entry = {
            "process": process_code,
            "latency": f"{latency:.4f}",
            "outcome": outcome
        }

        try:
            if LOG_PATH.exists():
                with open(LOG_PATH, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            else:
                logs = {}
        except Exception:
            logs = {}

        if initial_timestamp not in logs:
            logs[initial_timestamp] = []

        logs[initial_timestamp].append(log_entry)

        with open(LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=4)

    def handle_classifier_received(self, uploaded_file):
        initial_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        start_time = time.perf_counter()

        metadata = self.classifier_controller.save_uploaded_classifier(uploaded_file)

        deployment_info = self.classifier_controller.deploy_classifier(
            metadata["classifier_id"],
            metadata["model_filename"]
        )

        latency = time.perf_counter() - start_time

        self._log_event(
            initial_timestamp=initial_timestamp,
            process_code="P1",
            latency=latency,
            outcome=f"Classifier deployed: {deployment_info['classifier_id']}"
        )

        print(f"[ProductionSystemOrchestrator] Classifier deployed: {deployment_info}")
        return deployment_info

    def handle_session_received(self, session: dict):
        initial_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        start_time = time.perf_counter()

        with open(LATEST_SESSION_PATH, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=4)

        classification_result = self.classifier_controller.classify(session)

        with open(LATEST_LABEL_PATH, "w", encoding="utf-8") as f:
            json.dump(classification_result, f, indent=4)

        latency = time.perf_counter() - start_time

        self._log_event(
            initial_timestamp=initial_timestamp,
            process_code="P2",
            latency=latency,
            outcome=f"Predicted rating: {classification_result['rating']} for {classification_result['player_id']}"
        )

        print(f"[ProductionSystemOrchestrator] Session classified: {classification_result}")
        return classification_result

    def process_classification_result(self, classification_result: dict, communication_controller):
        initial_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        start_client = time.perf_counter()
        client_response = communication_controller.send_label_to_client(classification_result)
        client_latency = time.perf_counter() - start_client

        self._log_event(
            initial_timestamp=initial_timestamp,
            process_code="P3",
            latency=client_latency,
            outcome=f"Client-side send: {client_response['status']}"
        )

        start_eval = time.perf_counter()
        evaluation_response = self.evaluation_sender.send_label_to_evaluation(classification_result)
        evaluation_latency = time.perf_counter() - start_eval

        self._log_event(
            initial_timestamp=initial_timestamp,
            process_code="P4",
            latency=evaluation_latency,
            outcome=f"Evaluation send: {evaluation_response['status']}"
        )

        delivery_info = {
            "client": client_response,
            "evaluation": evaluation_response
        }

        print(f"[ProductionSystemOrchestrator] Outputs sent: {delivery_info}")
        return delivery_info