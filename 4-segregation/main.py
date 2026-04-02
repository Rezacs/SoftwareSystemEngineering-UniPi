"""Runs the Segregation System orchestrator locally without starting the REST server."""

from src.orchestrator import SegregationSystemOrchestrator
from src.communication_controller import CommunicationController


def main():
    result = SegregationSystemOrchestrator().run()
    if result.get("status") == "calibration_sets_sent":
        calibration_set = result.get("calibration_set")
        sent, details = CommunicationController().send_calibration_set(calibration_set)
        result["calibration_set_delivery"] = {
            "sent": sent,
            "details": details,
        }
    print(result)


if __name__ == "__main__":
    main()
