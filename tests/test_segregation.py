from segregation.orchestrator import SegregationSystemOrchestrator

orchestrator = SegregationSystemOrchestrator()
learning_sets = orchestrator.run()

print("Generated learning sets:")
print(learning_sets)