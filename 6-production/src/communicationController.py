from flask import Flask, request, jsonify
import requests

from src.config import (
    PRODUCTION_HOST,
    PRODUCTION_PORT,
    CLASSIFIER_RECEIVED_ENDPOINT,
    PREPARED_SESSION_RECEIVED_ENDPOINT,
    CLIENT_SIDE_LABEL_URL,
    MESSAGING_CONFIGURATION_URL
)


class CommunicationController:
    def __init__(self, orchestrator):
        self.app = Flask(__name__)
        self.orchestrator = orchestrator
        self._register_routes()

    def _register_routes(self):

        # =========================
        # BPMN: Classifier Received
        # =========================
        @self.app.route(CLASSIFIER_RECEIVED_ENDPOINT, methods=["POST"])
        def classifier_received():
            data = request.json

            try:
                deployment_info = self.orchestrator.handle_classifier_received(data)

                # BPMN: Configuration Sent → Messaging System
                config_response = self.send_configuration_to_messaging(deployment_info)

                return jsonify({
                    "status": "classifier_deployed",
                    "deployment": deployment_info,
                    "messaging": config_response
                })

            except Exception as e:
                return jsonify({"error": str(e)}), 500

        # =========================
        # BPMN: Prepared Session Received
        # =========================
        @self.app.route(PREPARED_SESSION_RECEIVED_ENDPOINT, methods=["POST"])
        def session_received():
            data = request.json

            try:
                # Classify
                classification_result = self.orchestrator.handle_session_received(data)

                # Send results (Client + Evaluation)
                send_result = self.orchestrator.process_classification_result(
                    classification_result,
                    self
                )

                return jsonify({
                    "status": "classified",
                    "result": classification_result,
                    "delivery": send_result
                })

            except Exception as e:
                return jsonify({"error": str(e)}), 500

    # =========================
    # BPMN: Label Sent → Client-side
    # =========================
    def send_label_to_client(self, classification_result: dict):
        try:
            response = requests.post(CLIENT_SIDE_LABEL_URL, json=classification_result)
            return {
                "status": "sent",
                "response_code": response.status_code
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    # =========================
    # BPMN: Configuration Sent → Messaging System
    # =========================
    def send_configuration_to_messaging(self, deployment_info: dict):
        try:
            response = requests.post(MESSAGING_CONFIGURATION_URL, json=deployment_info)
            return {
                "status": "sent",
                "response_code": response.status_code
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def run(self):
        self.app.run(host=PRODUCTION_HOST, port=PRODUCTION_PORT)