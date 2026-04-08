
from ingestion.orchestrator import IngestionSystemOrchestrator

if __name__ == "__main__":
    orchestrator = IngestionSystemOrchestrator()
    orchestrator.start()