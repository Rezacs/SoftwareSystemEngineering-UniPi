import json

import requests
from flask import Flask, jsonify, request

from src.config import (
    PRODUCTION_HOST,
    PRODUCTION_PORT,
    CLASSIFIER_RECEIVED_ENDPOINT,
    PREPARED_SESSION_RECEIVED_ENDPOINT,
    STATUS_ENDPOINT,
    CLIENT_SIDE_LABEL_URL,
    MESSAGING_CONFIGURATION_URL,
    LATEST_CLASSIFIER_PATH,
    LATEST_SESSION_PATH,
    LATEST_LABEL_PATH,
    LOG_PATH
)


class CommunicationController:
    def __init__(self, orchestrator):
        self.app = Flask(__name__)
        self.orchestrator = orchestrator
        self._register_routes()

    def _register_routes(self):
        @self.app.route(CLASSIFIER_RECEIVED_ENDPOINT, methods=["POST"])
        def classifier_received():
            try:
                if "classifier" not in request.files:
                    return jsonify({"error": "Missing classifier file"}), 400

                uploaded_file = request.files["classifier"]

                deployment_info = self.orchestrator.handle_classifier_received(uploaded_file)
                config_response = self.send_configuration_to_messaging(deployment_info)

                return jsonify({
                    "status": "classifier_deployed",
                    "deployment": deployment_info,
                    "messaging": config_response
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route(PREPARED_SESSION_RECEIVED_ENDPOINT, methods=["POST"])
        def session_received():
            try:
                data = request.get_json()

                classification_result = self.orchestrator.handle_session_received(data)
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

        @self.app.route(STATUS_ENDPOINT, methods=["GET"])
        def get_status():
            def read_json(path, default):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    return default

            return jsonify({
                "classifier": read_json(LATEST_CLASSIFIER_PATH, {}),
                "session": read_json(LATEST_SESSION_PATH, {}),
                "label": read_json(LATEST_LABEL_PATH, {}),
                "logs": read_json(LOG_PATH, [])
            })

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