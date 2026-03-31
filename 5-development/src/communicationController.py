"""
CommunicationController
=======================
Handles all network I/O for the Development System:

  INBOUND  — Flask REST server that receives the learning-set payload
             from the Data-Collection system.

  OUTBOUND — Two targeted POST operations only:
               • send the classifier (.sav) to the Production System
                 when the test passes.
               • send the testing report (JSON) to the Monitoring System
                 when the test does not pass.

Network addresses are configured as constants at the top of this file.
"""

import json
import os
import threading
from typing import Callable, Optional

import requests
from flask import Flask, Response, jsonify, request


# ---------------------------------------------------------------------------
# ── Network configuration — edit these to match your deployment ────────────
# ---------------------------------------------------------------------------

# Machine that sends us the learning-set payload
SEGREGATION_SYSTEM_IP   = "192.168.1.10"   # IP of the Data-Collection system
SEGREGATION_SYSTEM_PORT = 5000

# Machine that receives the trained classifier when the test passes
PRODUCTION_SYSTEM_IP   = "192.168.1.20"   # IP of the Production System
PRODUCTION_SYSTEM_PORT = 5000
PRODUCTION_ENDPOINT    = "/classifier"

# Machine that receives the testing report when the test does NOT pass
MESSAGING_SYSTEM_IP   = "192.168.1.30"   # IP of the Monitoring System
MESSAGING_SYSTEM_PORT = 5000
MESSAGING_ENDPOINT    = "/report"

# This machine
LISTEN_HOST = "0.0.0.0"   # listen on all interfaces
LISTEN_PORT = 5000


# ---------------------------------------------------------------------------

class CommunicationController:
    """
    Manages inbound and outbound HTTP communication.

    Inbound : Flask REST server on LISTEN_PORT.
    Outbound: targeted POSTs to Production System or Monitoring System.
    """

    def __init__(
        self,
        received_data_path: str = "data/internal/received_data.json",
    ) -> None:
        self._received_data_path             = received_data_path
        self._app: Flask                     = Flask(__name__)
        self._on_data_received: Optional[Callable[[dict], None]] = None
        self._register_routes()

    # -----------------------------------------------------------------------
    # INBOUND — Flask server
    # -----------------------------------------------------------------------

    def _register_routes(self) -> None:

        @self._app.route("/data", methods=["POST"])
        def receive_data() -> Response:
            """
            Receives the learning-set JSON payload from the Data-Collection
            system.  Persists it to disk, then notifies the orchestrator.
            """
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400

            payload: dict = request.get_json(force=True)

            os.makedirs(os.path.dirname(self._received_data_path), exist_ok=True)
            with open(self._received_data_path, "w", encoding="UTF-8") as f:
                json.dump(payload, f, indent="\t")

            print(
                f"[CommunicationController] Payload received from "
                f"{SEGREGATION_SYSTEM_IP}:{SEGREGATION_SYSTEM_PORT} → saved to {self._received_data_path}"
            )

            if self._on_data_received is not None:
                self._on_data_received(payload)

            return jsonify({"status": "ok"}), 200

        @self._app.route("/health", methods=["GET"])
        def health() -> Response:
            """Liveness probe."""
            return jsonify({"status": "running"}), 200

    def start_server(self, on_data_received: Callable[[dict], None]) -> None:
        """
        Start the Flask server in a daemon thread.

        Parameters
        ----------
        on_data_received :
            Called by /data once the payload is saved.
            Typically ``main.handle_message``.
        """
        self._on_data_received = on_data_received

        thread = threading.Thread(
            target=lambda: self._app.run(
                host=LISTEN_HOST,
                port=LISTEN_PORT,
                debug=False,
                use_reloader=False,
            ),
            daemon=True,
        )
        thread.start()
        print(
            f"[CommunicationController] Listening on "
            f"http://{LISTEN_HOST}:{LISTEN_PORT}  "
            f"(expecting sender: {SEGREGATION_SYSTEM_IP}:{SEGREGATION_SYSTEM_PORT})"
        )

    # -----------------------------------------------------------------------
    # OUTBOUND — two operations only
    # -----------------------------------------------------------------------

    @staticmethod
    def _post_json(url: str, payload: dict, timeout: int = 10) -> bool:
        """Low-level JSON POST helper."""
        try:
            r = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=timeout,
            )
            r.raise_for_status()
            print(f"[CommunicationController] JSON sent → {url} ({r.status_code})")
            return True
        except requests.exceptions.RequestException as exc:
            print(f"[CommunicationController] POST failed → {url}: {exc}")
            return False

    @staticmethod
    def _post_file(url: str, file_path: str, field: str, mime: str, timeout: int = 30) -> bool:
        """Low-level multipart file POST helper."""
        try:
            with open(file_path, "rb") as fh:
                r = requests.post(
                    url,
                    files={field: (os.path.basename(file_path), fh, mime)},
                    timeout=timeout,
                )
            r.raise_for_status()
            print(f"[CommunicationController] File sent → {url} ({r.status_code})")
            return True
        except FileNotFoundError:
            print(f"[CommunicationController] File not found: {file_path}")
            return False
        except requests.exceptions.RequestException as exc:
            print(f"[CommunicationController] POST failed → {url}: {exc}")
            return False

    # ── Public API ──────────────────────────────────────────────────────────

    def send_classifier(self, model_path: str) -> bool:
        """
        Send the trained classifier (.sav file) to the Production System.
        Called when the testing phase PASSES.

        Parameters
        ----------
        model_path : local path to the joblib-serialised model file.
        """
        url = (
            f"http://{PRODUCTION_SYSTEM_IP}:{PRODUCTION_SYSTEM_PORT}"
            f"{PRODUCTION_ENDPOINT}"
        )
        print(
            f"[CommunicationController] Sending classifier to "
            f"Production System ({PRODUCTION_SYSTEM_IP}:{PRODUCTION_SYSTEM_PORT}) …"
        )
        return self._post_file(url, model_path, field="classifier", mime="application/octet-stream")

    def send_testing_report(self, report_path: str) -> bool:
        """
        Send the testing report (JSON) to the Monitoring System.
        Called when the testing phase DOES NOT PASS.

        Parameters
        ----------
        report_path : local path to the testing_report.json file.
        """
        url = (
            f"http://{MESSAGING_SYSTEM_IP}:{MESSAGING_SYSTEM_PORT}"
            f"{MESSAGING_ENDPOINT}"
        )
        print(
            f"[CommunicationController] Sending testing report to "
            f"Messaging System ({MESSAGING_SYSTEM_IP}:{MESSAGING_SYSTEM_PORT}) …"
        )
        try:
            with open(report_path, "r", encoding="UTF-8") as f:
                payload = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            print(f"[CommunicationController] Cannot read report: {exc}")
            return False
        return self._post_json(url, payload)