from src.config import ensure_directories
from src.productionSystemOrchestrator import ProductionSystemOrchestrator
from src.communicationController import CommunicationController
import webbrowser
from pathlib import Path


if __name__ == "__main__":
    print("=== Production System ===")

    ensure_directories()

    dashboard_path = Path(__file__).resolve().parent / "frontend" / "dashboard.html"
    webbrowser.open(dashboard_path.as_uri())

    orchestrator = ProductionSystemOrchestrator()
    communication_controller = CommunicationController(orchestrator)

    print("Production System is running...")
    print("Waiting for:")
    print("- Classifier Received (from Development)")
    print("- Prepared Session Received (from Preparation)")

    # process already existing session automatically

    communication_controller.run()



    