"""
CommunicationController
=======================
INBOUND  — Flask REST server receives the learning-set payload
           from the Segregation System.

OUTBOUND — Two operations only:
             • send_classifier()     → POST .sav to Production System (test passes)
             • save_rejected_report()→ saves testing report locally as JSON (test fails)

All network configuration is read from config.json, which is loaded
by DevelopmentSystemOrchestrator and passed in at construction time.
"""

import json
import os
import threading
from typing import Callable, Optional

import requests
from flask import Flask, Response, jsonify, request


class CommunicationController:
    """
    Parameters
    ----------
    listen_host          : interface to bind the Flask server on
    listen_port          : port for the Flask server
    segregation_ip       : IP of the system sending the payload (for logging)
    segregation_port     : port of the sender (for logging)
    production_ip        : IP of the Production System (classifier destination)
    production_port      : port of the Production System
    production_endpoint  : endpoint on the Production System
    received_data_path   : where incoming payloads are saved to disk
    rejected_report_path : where the testing report is saved when test fails
    """

    def __init__(
        self,
        listen_host: str,
        listen_port: int,
        segregation_ip: str,
        segregation_port: int,
        production_ip: str,
        production_port: int,
        production_endpoint: str,
        received_data_path: str,
        rejected_report_path: str,
    ) -> None:
        self._listen_host          = listen_host
        self._listen_port          = listen_port
        self._segregation_ip       = segregation_ip
        self._segregation_port     = segregation_port
        self._production_ip        = production_ip
        self._production_port      = production_port
        self._production_endpoint  = production_endpoint
        self._received_data_path   = received_data_path
        self._rejected_report_path = rejected_report_path

        self._app: Flask = Flask(__name__)
        self._on_data_received: Optional[Callable[[dict], None]] = None
        self._register_routes()

    # ── INBOUND — Flask server ─────────────────────────────────────────

    def _register_routes(self) -> None:

        @self._app.route("/data", methods=["POST"])
        def receive_data() -> Response:
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400

            payload: dict = request.get_json(force=True)

            os.makedirs(os.path.dirname(self._received_data_path), exist_ok=True)
            with open(self._received_data_path, "w", encoding="UTF-8") as f:
                json.dump(payload, f, indent="\t")

            print(
                f"[CommunicationController] Payload received from "
                f"{self._segregation_ip}:{self._segregation_port} "
                f"→ saved to {self._received_data_path}"
            )

            if self._on_data_received is not None:
                self._on_data_received(payload)

            return jsonify({"status": "ok"}), 200

        @self._app.route("/health", methods=["GET"])
        def health() -> Response:
            return jsonify({"status": "running"}), 200

    def start_server(self, on_data_received: Callable[[dict], None]) -> None:
        """Start the Flask server in a daemon thread."""
        self._on_data_received = on_data_received

        thread = threading.Thread(
            target=lambda: self._app.run(
                host=self._listen_host,
                port=self._listen_port,
                debug=False,
                use_reloader=False,
            ),
            daemon=True,
        )
        thread.start()
        print(
            f"[CommunicationController] Listening on "
            f"http://{self._listen_host}:{self._listen_port}  "
            f"(expecting sender: {self._segregation_ip}:{self._segregation_port})"
        )

    # ── OUTBOUND ───────────────────────────────────────────────────────

    def send_classifier(self, model_path: str) -> bool:
        """
        BPMN: CLASSIFIER SENT
        POST the trained .sav file to the Production System.
        Called by test_passed() when approved = True.
        """
        url = (
            f"http://{self._production_ip}:{self._production_port}"
            f"{self._production_endpoint}"
        )
        print(
            f"[CommunicationController] CLASSIFIER SENT → "
            f"{self._production_ip}:{self._production_port} …"
        )
        try:
            with open(model_path, "rb") as fh:
                r = requests.post(
                    url,
                    files={"classifier": (os.path.basename(model_path), fh, "application/octet-stream")},
                    timeout=30,
                )
            r.raise_for_status()
            print(f"[CommunicationController] Classifier sent successfully ({r.status_code})")
            return True
        except FileNotFoundError:
            print(f"[CommunicationController] Model file not found: {model_path}")
            return False
        except requests.exceptions.RequestException as exc:
            print(f"[CommunicationController] POST failed: {exc}")
            return False

    def save_rejected_report(self, report_path: str) -> bool:
        """
        BPMN: CONFIGURATION SENT (no external messaging system)
        Saves the testing report JSON locally so it can be reviewed.
        Called by test_passed() when approved = False.
        """
        try:
            with open(report_path, "r", encoding="UTF-8") as f:
                report = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            print(f"[CommunicationController] Cannot read report: {exc}")
            return False

        os.makedirs(os.path.dirname(self._rejected_report_path), exist_ok=True)
        with open(self._rejected_report_path, "w", encoding="UTF-8") as f:
            json.dump(report, f, indent="\t")

        print(
            f"[CommunicationController] Rejected report saved → "
            f"{self._rejected_report_path}"
        )
        return True