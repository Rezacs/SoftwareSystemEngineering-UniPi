from evaluation.orchestrator import EvaluationSystemOrchestrator

orchestrator = EvaluationSystemOrchestrator()
report = orchestrator.run()

print("Evaluation report:")
print(report)