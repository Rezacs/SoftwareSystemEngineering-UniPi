"""
CommunicationController
=======================
Handles all network I/O for the Development System:

  INBOUND  — Flask REST server that receives JSON payloads (e.g. a
             LearningSet from the Data-Collection system) and saves
             them to disk, then notifies the orchestrator.

  OUTBOUND — POST helpers that send JSON reports and PNG images to
             other systems identified by their IP address.

Both directions use the same JSON-over-HTTP convention agreed across
the pipeline (point VI of the project specification).
"""

import json
import os
import threading
from typing import Callable, Optional

import requests
from flask import Flask, Response, jsonify, request


# ---------------------------------------------------------------------------
# Default network settings  (override via constructor)
# ---------------------------------------------------------------------------
DEFAULT_HOST = "0.0.0.0"   # listen on all interfaces
DEFAULT_PORT = 5000


class CommunicationController:
    """
    Manages inbound and outbound HTTP communication.

    Parameters
    ----------
    host : str
        Interface the Flask server listens on.
    port : int
        Port the Flask server listens on.
    received_data_path : str
        Where incoming JSON payloads are persisted before the
        orchestrator processes them.
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        received_data_path: str = "data/internal/received_data.json",
    ) -> None:
        self._host               = host
        self._port               = port
        self._received_data_path = received_data_path

        self._app                        = Flask(__name__)
        self._on_data_received: Optional[Callable[[dict], None]] = None

        self._register_routes()

    # -----------------------------------------------------------------------
    # INBOUND — Flask server
    # -----------------------------------------------------------------------

    def _register_routes(self) -> None:
        """Attach all REST endpoints to the Flask app."""

        @self._app.route("/data", methods=["POST"])
        def receive_data() -> Response:
            """
            Endpoint for receiving a JSON payload from another system.
            Expected content-type: application/json

            The payload is:
              1. Validated as JSON.
              2. Persisted to ``received_data_path``.
              3. Forwarded to the registered callback (orchestrator).

            Returns 200 on success, 400 on bad input.
            """
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 400

            payload: dict = request.get_json(force=True)

            # Persist raw payload so the orchestrator can reload it after restart
            os.makedirs(os.path.dirname(self._received_data_path), exist_ok=True)
            with open(self._received_data_path, "w", encoding="UTF-8") as f:
                json.dump(payload, f, indent="\t")

            print(f"[CommunicationController] Received data → saved to {self._received_data_path}")

            # Notify orchestrator if a callback is registered
            if self._on_data_received is not None:
                self._on_data_received(payload)

            return jsonify({"status": "ok"}), 200

        @self._app.route("/health", methods=["GET"])
        def health() -> Response:
            """Simple liveness probe so other machines can check we are up."""
            return jsonify({"status": "running"}), 200

    def start_server(self, on_data_received: Callable[[dict], None]) -> None:
        """
        Start the Flask server in a **daemon thread** so it does not
        block the main orchestrator thread.

        Parameters
        ----------
        on_data_received : Callable[[dict], None]
            Function called by the /data endpoint once a payload has
            been saved.  Typically ``orchestrator.handle_message``.
        """
        self._on_data_received = on_data_received

        flask_thread = threading.Thread(
            target=lambda: self._app.run(
                host=self._host,
                port=self._port,
                debug=False,
                use_reloader=False,   # must be False inside a thread
            ),
            daemon=True,             # dies automatically when main process exits
        )
        flask_thread.start()
        print(
            f"[CommunicationController] REST server listening on "
            f"http://{self._host}:{self._port}"
        )

    # -----------------------------------------------------------------------
    # OUTBOUND — POST helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _build_url(ip: str, port: int, endpoint: str) -> str:
        """Construct a full URL from components."""
        endpoint = endpoint.lstrip("/")
        return f"http://{ip}:{port}/{endpoint}"

    def send_json(
        self,
        target_ip: str,
        payload: dict,
        target_port: int = DEFAULT_PORT,
        endpoint: str = "/data",
        timeout: int = 10,
    ) -> bool:
        """
        POST a JSON payload to another machine.

        Parameters
        ----------
        target_ip   : IP address (or hostname) of the target machine.
        payload     : Dictionary that will be serialised as JSON.
        target_port : Port on the target machine (default 5000).
        endpoint    : URL path on the target machine (default /data).
        timeout     : Request timeout in seconds.

        Returns
        -------
        True if the request succeeded (HTTP 2xx), False otherwise.
        """
        url = self._build_url(target_ip, target_port, endpoint)
        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=timeout,
            )
            response.raise_for_status()
            print(f"[CommunicationController] JSON sent to {url} → {response.status_code}")
            return True
        except requests.exceptions.RequestException as exc:
            print(f"[CommunicationController] Failed to send JSON to {url}: {exc}")
            return False

    def send_json_file(
        self,
        target_ip: str,
        json_path: str,
        target_port: int = DEFAULT_PORT,
        endpoint: str = "/data",
        timeout: int = 10,
    ) -> bool:
        """
        Read a JSON file from disk and POST it to another machine.

        Parameters
        ----------
        target_ip  : IP address of the target machine.
        json_path  : Local path to the .json file to send.
        """
        try:
            with open(json_path, "r", encoding="UTF-8") as f:
                payload = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            print(f"[CommunicationController] Cannot read {json_path}: {exc}")
            return False

        return self.send_json(target_ip, payload, target_port, endpoint, timeout)

    def send_png(
        self,
        target_ip: str,
        png_path: str,
        target_port: int = DEFAULT_PORT,
        endpoint: str = "/image",
        timeout: int = 10,
    ) -> bool:
        """
        POST a PNG file as multipart/form-data to another machine.

        The receiving endpoint is expected to accept a file field
        named ``"file"``.

        Parameters
        ----------
        target_ip : IP address of the target machine.
        png_path  : Local path to the .png file to send.
        """
        url = self._build_url(target_ip, target_port, endpoint)
        try:
            with open(png_path, "rb") as img:
                response = requests.post(
                    url,
                    files={"file": (os.path.basename(png_path), img, "image/png")},
                    timeout=timeout,
                )
            response.raise_for_status()
            print(f"[CommunicationController] PNG sent to {url} → {response.status_code}")
            return True
        except FileNotFoundError:
            print(f"[CommunicationController] PNG file not found: {png_path}")
            return False
        except requests.exceptions.RequestException as exc:
            print(f"[CommunicationController] Failed to send PNG to {url}: {exc}")
            return False

    # -----------------------------------------------------------------------
    # Convenience wrappers used by the orchestrator
    # -----------------------------------------------------------------------

    def send_validation_report(self, target_ip: str, json_path: str, **kwargs) -> bool:
        """Send the validation report JSON to another system."""
        return self.send_json_file(target_ip, json_path, **kwargs)

    def send_testing_report(self, target_ip: str, json_path: str, **kwargs) -> bool:
        """Send the testing report JSON to another system."""
        return self.send_json_file(target_ip, json_path, **kwargs)

    def send_learning_curve(self, target_ip: str, png_path: str, **kwargs) -> bool:
        """Send the learning-curve PNG to another system."""
        return self.send_png(target_ip, png_path, **kwargs)

    def send_classifier_report(
        self,
        target_ip: str,
        json_path: str,
        png_path: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        Send the final classifier report (JSON + optional PNG) to the
        Production System (or any downstream consumer).
        """
        ok = self.send_json_file(target_ip, json_path, **kwargs)
        if png_path and os.path.isfile(png_path):
            ok = self.send_png(target_ip, png_path, **kwargs) and ok
        return ok