"""Exposes the REST API of the Segregation System and forwards external requests to the internal workflow."""

import json
from urllib import error, request

from flask import Flask, jsonify, request as flask_request, send_file

from . import (
    BALANCING_PLOT_OUTPUT_PATH,
    BALANCING_REPORT_ENDPOINT,
    BALANCING_REPORT_OUTPUT_PATH,
    BALANCING_PLOT_ENDPOINT,
    CALIBRATION_SET_OUTPUT_PATH,
    CALIBRATION_SET_ENDPOINT,
    CONFIG_PATH,
    COVERAGE_PLOT_OUTPUT_PATH,
    COVERAGE_REPORT_ENDPOINT,
    COVERAGE_REPORT_OUTPUT_PATH,
    COVERAGE_PLOT_ENDPOINT,
    HEALTH_ENDPOINT,
    SEGREGATION_DB_PATH,
    PREPARED_SESSION_INPUT_PATH,
    PREPARED_SESSIONS_ENDPOINT,
    PROJECT_ROOT,
    SEGREGATION_WORKFLOW_STATE_PATH,
    WORKFLOW_STATE_ENDPOINT,
)
from .session_repository import SessionRepository
from .utils.json_io import JsonIO
from .utils.schema_validator import SchemaValidator


class CommunicationController:
    def __init__(self):
        self.config = JsonIO.load(CONFIG_PATH)
        self.session_repository = SessionRepository()
        self.validator = SchemaValidator(
            str(PROJECT_ROOT / "data" / "schema" / "prepared_session_schema.json")
        )

    def load_workflow_state(self) -> dict:
        try:
            return JsonIO.load(SEGREGATION_WORKFLOW_STATE_PATH)
        except FileNotFoundError:
            return {"phase": "idle"}

    def is_server_running(self) -> bool:
        health_url = (
            f"http://{self.config['segregationSystemIpAddress']}:"
            f"{self.config['segregationSystemPort']}"
            f"{HEALTH_ENDPOINT}"
        )
        try:
            with request.urlopen(health_url, timeout=2) as response:
                return response.status == 200
        except Exception:
            return False

    def send_json(self, url: str, json_data: dict) -> tuple[bool, str]:
        data = json.dumps(json_data).encode("utf-8")
        req = request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=5) as response:
                return True, response.read().decode("utf-8")
        except error.URLError as exc:
            return False, str(exc)

    def send_calibration_set(self, calibration_set: dict) -> tuple[bool, str]:
        target_url = self.config.get("developmentSystemEndpoint", "").strip()
        if not target_url:
            return False, "developmentSystemEndpoint not configured"
        return self.send_json(target_url, calibration_set)

    def create_app(self) -> Flask:
        app = Flask(__name__)

        @app.get(HEALTH_ENDPOINT)
        def health():
            return jsonify({"status": "ok", "service": "segregation_system"})

        @app.post(PREPARED_SESSIONS_ENDPOINT)
        def receive_prepared_session():
            payload = flask_request.get_json(silent=True)
            is_valid, message = self.validator.validatePreparedSession(payload)
            if not is_valid:
                return jsonify({"status": "invalid_payload", "details": message}), 400

            self.session_repository.initialize(SEGREGATION_DB_PATH)

            workflow_state = self.load_workflow_state()
            batch_is_open = workflow_state["phase"] not in {
                "waiting_balancing_decision",
                "waiting_coverage_decision",
            }
            self.session_repository.store(
                payload,
                SEGREGATION_DB_PATH,
                to_process=batch_is_open,
            )
            to_process_count = self.session_repository.sessions_count(
                SEGREGATION_DB_PATH,
                to_process_only=True,
            )
            print(
                f"[API] Prepared session received. to_process sessions counter: {to_process_count}"
            )
            JsonIO.save(PREPARED_SESSION_INPUT_PATH, payload)
            return jsonify(
                {
                    "status": "prepared_session_received",
                    "stored_in_db": True,
                    "input_path": PREPARED_SESSION_INPUT_PATH,
                }
            )

        @app.get(WORKFLOW_STATE_ENDPOINT)
        def get_workflow_state():
            return jsonify(JsonIO.load(SEGREGATION_WORKFLOW_STATE_PATH))

        @app.get(BALANCING_REPORT_ENDPOINT)
        def get_balancing_report():
            return jsonify(JsonIO.load(BALANCING_REPORT_OUTPUT_PATH))

        @app.get(COVERAGE_REPORT_ENDPOINT)
        def get_coverage_report():
            return jsonify(JsonIO.load(COVERAGE_REPORT_OUTPUT_PATH))

        @app.get(BALANCING_PLOT_ENDPOINT)
        def get_balancing_plot():
            return send_file(BALANCING_PLOT_OUTPUT_PATH, mimetype="image/png")

        @app.get(COVERAGE_PLOT_ENDPOINT)
        def get_coverage_plot():
            return send_file(COVERAGE_PLOT_OUTPUT_PATH, mimetype="image/png")

        @app.get(CALIBRATION_SET_ENDPOINT)
        def get_calibration_set():
            return jsonify(JsonIO.load(CALIBRATION_SET_OUTPUT_PATH))

        return app

    def start_server(self):
        app = self.create_app()
        app.run(
            host=self.config["segregationSystemIpAddress"],
            port=self.config["segregationSystemPort"],
            debug=False,
        )
