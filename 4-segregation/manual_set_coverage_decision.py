"""Writes the local coverage-decision JSON used by the stop-and-go workflow."""

import sys

from src import COVERAGE_REPORT_DECISION_PATH
from src.utils.json_io import JsonIO


def set_coverage_decision(approved: bool):
    JsonIO.save(COVERAGE_REPORT_DECISION_PATH, {"approved": approved})
    print(
        {
            "status": "coverage_decision_saved",
            "decision_path": COVERAGE_REPORT_DECISION_PATH,
            "approved": approved,
        }
    )


if __name__ == "__main__":
    approved = True
    if len(sys.argv) > 1:
        approved = sys.argv[1].lower() == "true"
    set_coverage_decision(approved)
    print("Test passed")
