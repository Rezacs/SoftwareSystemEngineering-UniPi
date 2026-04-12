from src.config import ensure_directories
from src.productionSystemOrchestrator import ProductionSystemOrchestrator
from src.communicationController import CommunicationController
from pathlib import Path

if __name__ == "__main__":
    print("=== Production System ===")

    ensure_directories()

    orchestrator = ProductionSystemOrchestrator()
    communication_controller = CommunicationController(orchestrator)

    print("Production System is running...")
    print("Waiting for:")
    print("- Classifier Received (from Development)")
    print("- Prepared Session Received (from Preparation)")

    communication_controller.run()