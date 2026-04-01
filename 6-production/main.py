from src.config import ensure_directories
from src.productionSystemOrchestrator import ProductionSystemOrchestrator
from src.communicationController import CommunicationController


def main():
    print("=== Production System ===")

    # Ensure folders exist
    ensure_directories()

    # Initialize core components
    orchestrator = ProductionSystemOrchestrator()
    communication_controller = CommunicationController(orchestrator)

    print("Production System is running...")
    print("Waiting for:")
    print("- Classifier Received (from Development)")
    print("- Prepared Session Received (from Preparation)")

    # Start server
    communication_controller.run()


if __name__ == "__main__":
    main()