"""Writes the local coverage-decision JSON used by the stop-and-go workflow."""

import json
import sys

from src import COVERAGE_REPORT_DECISION_PATH
from src.utils.json_io import JsonIO


def set_coverage_decision(
    approved: bool,
    feature_comments: dict | None = None,
):
    payload = {"approved": approved}
    if isinstance(feature_comments, dict) and feature_comments:
        payload["featureComments"] = feature_comments

    JsonIO.save(COVERAGE_REPORT_DECISION_PATH, payload)
    print(
        {
            "status": "coverage_decision_saved",
            "decision_path": COVERAGE_REPORT_DECISION_PATH,
            "approved": approved,
            "featureComments": payload.get("featureComments", {}),
        }
    )


if __name__ == "__main__":
    approved = True
    feature_comments = None

    if len(sys.argv) > 1:
        approved = sys.argv[1].lower() == "true"
    if len(sys.argv) > 2:
        try:
            parsed = json.loads(sys.argv[2])
            if isinstance(parsed, dict):
                feature_comments = parsed
        except json.JSONDecodeError:
            feature_comments = None

    set_coverage_decision(approved, feature_comments)
    print("Test passed")
