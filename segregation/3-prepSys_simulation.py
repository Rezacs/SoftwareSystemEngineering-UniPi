"""Runs a mock upstream system that sends prepared sessions to the Segregation System via REST."""

import json
import time
from pathlib import Path

import requests
from flask import Flask, jsonify, request

from src import PREPARED_SESSIONS_ENDPOINT


PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.json"
INPUT_DIR = PROJECT_ROOT / "data" / "input"
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"
SEND_STATUS_PATH = OUTPUT_DIR / "sent_prepared_sessions_status.json"
MOCK_UPSTREAM_SYSTEM_PORT = 5001


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def save_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=4)


def load_prepared_sessions() -> list[tuple[str, dict]]:
    json_files = sorted(INPUT_DIR.glob("prepared_session*.json"))
    if not json_files:
        raise FileNotFoundError(
            f"No prepared-session JSON files found in {INPUT_DIR}"
        )

    prepared_sessions = []
    for json_filename in json_files:
        with json_filename.open("r", encoding="utf-8") as file:
            prepared_sessions.append((json_filename.name, json.load(file)))
    return prepared_sessions


def send_prepared_sessions(delay_seconds: float = 1.0) -> dict:
    config = load_config()
    url = (
        f"http://{config['segregationSystemIpAddress']}:"
        f"{config['segregationSystemPort']}"
        f"{PREPARED_SESSIONS_ENDPOINT}"
    )

    results = []
    for filename, payload in load_prepared_sessions():
        response = requests.post(url, json=payload, timeout=5)
        response_text = response.text
        try:
            response_body = response.json()
        except ValueError:
            response_body = response_text

        results.append(
            {
                "file": filename,
                "status_code": response.status_code,
                "ok": response.ok,
                "response": response_body,
            }
        )
        time.sleep(delay_seconds)

    overall_status = {
        "status": "prepared_sessions_sent",
        "target_url": url,
        "sent_count": len(results),
        "all_succeeded": all(result["ok"] for result in results),
        "results": results,
    }
    save_json(SEND_STATUS_PATH, overall_status)
    return overall_status


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "mock_upstream_system"})

    @app.get("/prepared-sessions/available")
    def list_prepared_sessions():
        files = [path.name for path in sorted(INPUT_DIR.glob("prepared_session*.json"))]
        return jsonify({"available_files": files, "count": len(files)})

    @app.post("/prepared-sessions/send")
    def send_batch():
        payload = request.get_json(silent=True) or {}
        delay_seconds = float(payload.get("delay_seconds", 1.0))

        try:
            status = send_prepared_sessions(delay_seconds=delay_seconds)
        except FileNotFoundError as exc:
            return jsonify({"status": "no_prepared_sessions", "details": str(exc)}), 404
        except requests.RequestException as exc:
            return jsonify({"status": "send_failed", "details": str(exc)}), 502

        http_status = 200 if status["all_succeeded"] else 502
        return jsonify(status), http_status

    @app.get("/prepared-sessions/last-send-status")
    def get_last_send_status():
        if not SEND_STATUS_PATH.exists():
            return jsonify({"status": "no_batch_sent_yet"}), 404
        with SEND_STATUS_PATH.open("r", encoding="utf-8") as file:
            return jsonify(json.load(file))

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=MOCK_UPSTREAM_SYSTEM_PORT, debug=False)
