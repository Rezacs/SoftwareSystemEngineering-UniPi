from ingestion.orchestrator import IngestionSystemOrchestrator

orchestrator = IngestionSystemOrchestrator()
raw_session = orchestrator.run()

print("Generated raw session:")
print(raw_session)