"""
    Evaluation System Orchestrator init module
"""
from src.evaluation_system_orchestrator import EvaluationSystemOrchestrator

# Prepare and run the Evaluation System Orchestrator
if __name__ == "__main__":
    print("Initializing Evaluation System...")
    app = EvaluationSystemOrchestrator()
    print("Orchestrator loaded successfully.")
    app.run()
    print("Evaluation System Shutting Down.")