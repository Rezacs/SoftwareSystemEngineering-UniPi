from segregation.orchestrator import SegregationSystemOrchestrator

orchestrator = SegregationSystemOrchestrator()
result = orchestrator.run()

print("Balancing report:")
print(result["balancing_report"])

print("\nCoverage report:")
print(result["coverage_report"])

print("\nLearning sets:")
print(result["learning_sets"])