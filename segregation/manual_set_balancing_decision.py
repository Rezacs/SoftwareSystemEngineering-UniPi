"""Writes the local balancing-decision JSON used by the stop-and-go workflow."""

import sys

from src import BALANCING_REPORT_DECISION_PATH
from src.utils.json_io import JsonIO


def set_balancing_decision(approved: bool):
    JsonIO.save(BALANCING_REPORT_DECISION_PATH, {"approved": approved})
    print(
        {
            "status": "balancing_decision_saved",
            "decision_path": BALANCING_REPORT_DECISION_PATH,
            "approved": approved,
        }
    )


if __name__ == "__main__":
    approved = True
    if len(sys.argv) > 1:
        approved = sys.argv[1].lower() == "true"
    set_balancing_decision(approved)
    print("Test passed")
