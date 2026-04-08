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
                print("[CommunicationController] /classifier called")

                if "classifier" not in request.files:
                    print("[CommunicationController] Missing classifier file in request")
                    return jsonify({"error": "Missing classifier file"}), 400

                uploaded_file = request.files["classifier"]

                if uploaded_file.filename == "":
                    print("[CommunicationController] Empty classifier filename")
                    return jsonify({"error": "Empty classifier filename"}), 400

                print(f"[CommunicationController] Received classifier file: {uploaded_file.filename}")

                deployment_info = self.orchestrator.handle_classifier_received(uploaded_file)

                config_response = self.send_configuration_to_messaging(deployment_info)

                print(f"[CommunicationController] Classifier deployment completed: {deployment_info}")

                return jsonify({
                    "status": "classifier_deployed",
                    "deployment": deployment_info,
                    "messaging": config_response
                }), 200

            except Exception as e:
                print(f"[CommunicationController] Error in /classifier: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route(PREPARED_SESSION_RECEIVED_ENDPOINT, methods=["POST"])
        def session_received():
            try:
                print("[CommunicationController] /session called")

                data = request.get_json()
                print(f"[CommunicationController] Received session payload: {data}")

                classification_result = self.orchestrator.handle_session_received(data)
                send_result = self.orchestrator.process_classification_result(
                    classification_result,
                    self
                )

                print(f"[CommunicationController] Session classified and outputs sent: {send_result}")

                return jsonify({
                    "status": "classified",
                    "result": classification_result,
                    "delivery": send_result
                }), 200

            except Exception as e:
                print(f"[CommunicationController] Error in /session: {e}")
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
        print(f"[CommunicationController] Sending label to Client-side: {classification_result}")
        try:
            response = requests.post(CLIENT_SIDE_LABEL_URL, json=classification_result, timeout=10)
            print(f"[CommunicationController] Label sent to Client-side ({response.status_code})")
            return {
                "status": "sent",
                "response_code": response.status_code
            }
        except Exception as e:
            print(f"[CommunicationController] Failed to send label to Client-side: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def send_configuration_to_messaging(self, deployment_info: dict):
        print(f"[CommunicationController] Sending configuration to Messaging System: {deployment_info}")
        try:
            response = requests.post(MESSAGING_CONFIGURATION_URL, json=deployment_info, timeout=10)
            print(f"[CommunicationController] Configuration sent to Messaging System ({response.status_code})")
            return {
                "status": "sent",
                "response_code": response.status_code
            }
        except Exception as e:
            print(f"[CommunicationController] Failed to send configuration to Messaging System: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def run(self):
        print(f"[CommunicationController] Production server running on http://{PRODUCTION_HOST}:{PRODUCTION_PORT}")
        self.app.run(host=PRODUCTION_HOST, port=PRODUCTION_PORT)