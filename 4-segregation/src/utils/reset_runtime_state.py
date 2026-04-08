"""Resets the local runtime state of the Segregation System for a clean test run."""

from pathlib import Path

from src import (
    BALANCING_REPORT_DECISION_PATH,
    BALANCING_REPORT_OUTPUT_PATH,
    BALANCING_PLOT_OUTPUT_PATH,
    CALIBRATION_SET_OUTPUT_PATH,
    COVERAGE_REPORT_DECISION_PATH,
    COVERAGE_REPORT_OUTPUT_PATH,
    COVERAGE_PLOT_OUTPUT_PATH,
    PREPARED_SESSION_INPUT_PATH,
    SEGREGATION_DB_PATH,
    SEGREGATION_WORKFLOW_STATE_PATH,
)
from src.utils.json_io import JsonIO


RESET_JSON_CONTENT = {
    CALIBRATION_SET_OUTPUT_PATH: {
        "training_set": [],
        "validation_set": [],
        "test_set": [],
    },
}

# Decision files should be deleted, not reset to a default value
# This allows testing mode to properly simulate decisions
FILES_TO_DELETE_DECISIONS = [
    BALANCING_REPORT_DECISION_PATH,
    COVERAGE_REPORT_DECISION_PATH,
]

FILES_TO_DELETE = [
    SEGREGATION_DB_PATH,
    SEGREGATION_WORKFLOW_STATE_PATH,
    BALANCING_REPORT_OUTPUT_PATH,
    COVERAGE_REPORT_OUTPUT_PATH,
    BALANCING_PLOT_OUTPUT_PATH,
    COVERAGE_PLOT_OUTPUT_PATH,
]

FILES_TO_RESET = [
    PREPARED_SESSION_INPUT_PATH,
]


def delete_file(path: str):
    file_path = Path(path)
    if file_path.exists():
        file_path.unlink()
        print(f"deleted: {file_path}")
    else:
        print(f"missing: {file_path}")


def reset_json_file(path: str, payload):
    JsonIO.save(path, payload)
    print(f"reset: {Path(path)}")


def main():
    for path in FILES_TO_DELETE:
        delete_file(path)

    for path in FILES_TO_RESET:
        delete_file(path)
    
    for path in FILES_TO_DELETE_DECISIONS:
        delete_file(path)

    for path, payload in RESET_JSON_CONTENT.items():
        reset_json_file(path, payload)

    print("runtime state reset complete")


if __name__ == "__main__":
    main()
