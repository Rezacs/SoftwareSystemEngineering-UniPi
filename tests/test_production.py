from production.orchestrator import ProductionSystemOrchestrator

orchestrator = ProductionSystemOrchestrator()
result = orchestrator.run()

print("Prediction result:")
print(result)