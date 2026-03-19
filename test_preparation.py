from preparation.orchestrator import PreparationSystemOrchestrator

orchestrator = PreparationSystemOrchestrator()
prepared_session = orchestrator.run()

print("Generated prepared session:")
print(prepared_session)