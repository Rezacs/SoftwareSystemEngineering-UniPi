from development.orchestrator import DevelopmentSystemOrchestrator

orchestrator = DevelopmentSystemOrchestrator()
result = orchestrator.run()

print("Training report:")
print(result["training_report"])

print("\nValidation report:")
print(result["validation_report"])

print("\nTesting report:")
print(result["testing_report"])