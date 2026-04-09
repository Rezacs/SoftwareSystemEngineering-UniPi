"""Runs a mock Development System that receives the calibration set via REST."""

import json
from pathlib import Path

from flask import Flask, jsonify, request

from src import CALIBRATION_SET_ENDPOINT


PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"
# RECEIVED_CALIBRATION_SET_PATH = OUTPUT_DIR / "received_calibration_set.json"
# RECEIVED_CALIBRATION_STATUS_PATH = OUTPUT_DIR / "received_calibration_set_status.json"
MOCK_DEVELOPMENT_SYSTEM_PORT = 5003

REQUIRED_SESSION_FIELDS = [
    "session_id",
    "player_id",
    "label",
    "skill_overall",
    "social_influence_score",
    "injuries_impact_score",
]


def save_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=4)


def validate_session(session: dict, set_name: str, index: int) -> list[str]:
    if not isinstance(session, dict):
        return [f"{set_name}[{index}] must be an object"]

    errors = []
    for field in REQUIRED_SESSION_FIELDS:
        if field not in session:
            errors.append(f"{set_name}[{index}] missing field '{field}'")

    numeric_fields = [
        "skill_overall",
        "social_influence_score",
        "injuries_impact_score",
    ]
    for field in numeric_fields:
        value = session.get(field)
        if field in session and not isinstance(value, (int, float)):
            errors.append(f"{set_name}[{index}] field '{field}' must be numeric")

    return errors


def validate_calibration_set(payload: dict) -> tuple[bool, list[str], dict]:
    if not isinstance(payload, dict):
        return False, ["Payload must be a JSON object"], {}

    expected_sets = ["training_set", "validation_set", "test_set"]
    errors = []
    counts = {}

    for set_name in expected_sets:
        current_set = payload.get(set_name)
        if not isinstance(current_set, list):
            errors.append(f"Field '{set_name}' must be a list")
            continue

        counts[set_name] = len(current_set)
        for index, session in enumerate(current_set):
            errors.extend(validate_session(session, set_name, index))

    total = sum(counts.values())
    metadata = {
        "counts": counts,
        "total_sessions": total,
    }
    return len(errors) == 0, errors, metadata


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "mock_development_system"})

    @app.post(CALIBRATION_SET_ENDPOINT)
    def receive_calibration_set():
        payload = request.get_json(silent=True)
        is_valid, errors, metadata = validate_calibration_set(payload)

        status_payload = {
            "status": "calibration_set_valid" if is_valid else "invalid_calibration_set",
            "valid": is_valid,
            "errors": errors,
            **metadata,
        }
        # save_json(RECEIVED_CALIBRATION_STATUS_PATH, status_payload)

        if is_valid:
            # save_json(RECEIVED_CALIBRATION_SET_PATH, payload)
            return jsonify(status_payload), 200

        return jsonify(status_payload), 400

    # @app.get("/last-calibration-set/status")
    # def get_last_status():
    #     if not RECEIVED_CALIBRATION_STATUS_PATH.exists():
    #         return jsonify({"status": "no_calibration_set_received"}), 404
    #     with RECEIVED_CALIBRATION_STATUS_PATH.open("r", encoding="utf-8") as file:
    #         return jsonify(json.load(file))

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=MOCK_DEVELOPMENT_SYSTEM_PORT, debug=False)
