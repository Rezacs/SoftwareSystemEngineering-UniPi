"""
CommunicationController
=======================
Handles all network I/O for the Development System.
All addresses, ports and endpoints are read from config.json
via src.config — edit that file to change network settings.

  INBOUND  — Flask REST server receives the learning-set payload
             from the Segregation System.

  OUTBOUND — Two targeted POST operations only:
               • send_classifier()      → Production System (test passes)
               • send_testing_report()  → Messaging System  (test fails)
"""

import json
import os
import threading
from typing import Callable, Optional

import requests
from flask import Flask, Response, jsonify, request

from src.config import (
    LISTEN_HOST, LISTEN_PORT,
    SEGREGATION_SYSTEM_IP, SEGREGATION_SYSTEM_PORT,
    PRODUCTION_SYSTEM_IP, PRODUCTION_SYSTEM_PORT, PRODUCTION_ENDPOINT,
    MESSAGING_SYSTEM_IP, MESSAGING_SYSTEM_PORT, MESSAGING_ENDPOINT,
    RECEIVED_DATA_PATH,
)


class CommunicationController:
    """
    Manages inbound and outbound HTTP communication.

    Inbound : Flask REST server on LISTEN_HOST:LISTEN_PORT.
    Outbound: targeted POSTs to Production System or Messaging System.
    """

    def __init__(
        self,
        received_data_path: str = RECEIVED_DATA_PATH,
    ) -> None:
        self._received_data_path             = received_data_path
        self._app: Flask                     = Flask(__name__)
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
                f"{SEGREGATION_SYSTEM_IP}:{SEGREGATION_SYSTEM_PORT} "
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

    # ── OUTBOUND — low-level helpers ───────────────────────────────────

    @staticmethod
    def _post_json(url: str, payload: dict, timeout: int = 10) -> bool:
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

    # ── OUTBOUND — public API ──────────────────────────────────────────

    def send_classifier(self, model_path: str) -> bool:
        """
        BPMN: CLASSIFIER SENT
        POST the trained .sav file to the Production System.
        Called when test_passed() → YES.
        """
        url = f"http://{PRODUCTION_SYSTEM_IP}:{PRODUCTION_SYSTEM_PORT}{PRODUCTION_ENDPOINT}"
        print(
            f"[CommunicationController] CLASSIFIER SENT → "
            f"{PRODUCTION_SYSTEM_IP}:{PRODUCTION_SYSTEM_PORT} …"
        )
        return self._post_file(url, model_path, field="classifier", mime="application/octet-stream")

    def send_testing_report(self, report_path: str) -> bool:
        """
        BPMN: CONFIGURATION SENT
        POST the testing report JSON to the Messaging System.
        Called when test_passed() → NO.
        """
        url = f"http://{MESSAGING_SYSTEM_IP}:{MESSAGING_SYSTEM_PORT}{MESSAGING_ENDPOINT}"
        print(
            f"[CommunicationController] CONFIGURATION SENT → "
            f"{MESSAGING_SYSTEM_IP}:{MESSAGING_SYSTEM_PORT} …"
        )
        try:
            with open(report_path, "r", encoding="UTF-8") as f:
                payload = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            print(f"[CommunicationController] Cannot read report: {exc}")
            return False
        return self._post_json(url, payload)