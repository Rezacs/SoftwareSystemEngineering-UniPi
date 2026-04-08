from src.config import ensure_directories
from src.productionSystemOrchestrator import ProductionSystemOrchestrator
from src.communicationController import CommunicationController
import webbrowser
import os


if __name__ == "__main__":
    print("=== Production System ===")

    ensure_directories()

    dashboard_path = os.path.abspath("frontend/dashboard.html")
    webbrowser.open(f"file://{dashboard_path}")

    orchestrator = ProductionSystemOrchestrator()
    communication_controller = CommunicationController(orchestrator)

    print("Production System is running...")
    print("Waiting for:")
    print("- Classifier Received (from Development)")
    print("- Prepared Session Received (from Preparation)")

    # process already existing session automatically

    communication_controller.run()



    