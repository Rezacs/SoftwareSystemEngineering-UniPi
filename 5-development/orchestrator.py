from common.json_io import JsonIO
from development.training_orchestrator import TrainingOrchestrator
from development.validation_orchestrator import ValidationOrchestrator
from development.testing_orchestrator import TestingOrchestrator


class DevelopmentSystemOrchestrator:
    def __init__(self):
        self.training_orchestrator = TrainingOrchestrator()
        self.validation_orchestrator = ValidationOrchestrator()
        self.testing_orchestrator = TestingOrchestrator()

    def run(
        self,
        input_path="data/outputs/learning_sets.json",
        training_report_path="data/outputs/training_report.json",
        validation_report_path="data/outputs/validation_report.json",
        testing_report_path="data/outputs/testing_report.json"
    ):
        learning_sets = JsonIO.load(input_path)

        training_report = self.training_orchestrator.run(learning_sets)
        JsonIO.save(training_report_path, training_report)

        validation_report = self.validation_orchestrator.run(learning_sets)
        JsonIO.save(validation_report_path, validation_report)

        best_model = validation_report["best_model"]
        testing_report = self.testing_orchestrator.run(learning_sets, best_model)
        JsonIO.save(testing_report_path, testing_report)

        return {
            "training_report": training_report,
            "validation_report": validation_report,
            "testing_report": testing_report
        }