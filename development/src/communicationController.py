import json
import threading
from pathlib import Path
from typing import Callable, Optional

import requests
from flask import Flask, Response, jsonify, request


class CommunicationController:
  

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
        self._received_data_path   = Path(received_data_path)
        self._rejected_report_path = Path(rejected_report_path)

        self._app: Flask = Flask(__name__)
        self._on_data_received: Optional[Callable[[dict], None]] = None
        self._register_routes()

    # ── INBOUND — Flask server ─────────────────────────────────────────

    # -- Inside CommunicationController._register_routes --

    def _register_routes(self) -> None:
        @self._app.route("/data", methods=["POST"])
        def receive_data() -> Response:
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400

            payload: dict = request.get_json(force=True)

            # --- NEW VALIDATION STEP ---
            try:
                self._validate_payload_structure(payload)
            except ValueError as e:
                print(f"[CommunicationController] Validation Failed: {e}")
                return jsonify({"error": str(e)}), 400
            # ---------------------------

            # Save RAW data for audit/debugging
            self._received_data_path.parent.mkdir(parents=True, exist_ok=True)
            with self._received_data_path.open("w", encoding="UTF-8") as f:
                json.dump(payload, f, indent="\t")

            if self._on_data_received is not None:
                self._on_data_received(payload)

            return jsonify({"status": "ok"}), 200

    def _validate_payload_structure(self, payload: dict) -> None:
        """Structural validation: check for required keys and types."""
        for split in ["training_set", "validation_set", "test_set"]:
            if split not in payload:
                raise ValueError(f"Missing '{split}' in payload")
            if not isinstance(payload[split], list):
                raise ValueError(f"'{split}' must be a list")
            if len(payload[split]) == 0:
                raise ValueError(f"'{split}' must not be empty")
            
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
            model_file = Path(model_path)
            with model_file.open("rb") as fh:
                r = requests.post(
                    url,
                    files={"classifier": (model_file.name, fh, "application/octet-stream")},
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
        report_path = Path(report_path)
        try:
            with report_path.open("r", encoding="UTF-8") as f:
                report = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            print(f"[CommunicationController] Cannot read report: {exc}")
            return False

        self._rejected_report_path.parent.mkdir(parents=True, exist_ok=True)
        with self._rejected_report_path.open("w", encoding="UTF-8") as f:
            json.dump(report, f, indent="\t")

        print(
            f"[CommunicationController] Rejected report saved → "
            f"{self._rejected_report_path}"
        )
        return True