from Data.classifier import Classifier
from Data.learningPlot import LearningPlot
from Data.validationReport import ValidationReport
from Data.testingReport import TestingReport
from Inputs.hyperParameters import HyperParameters
from Inputs.learningSet import LearningSet
from typing import List, Optional
class TestingOrchestrator:
    """Runs the final acceptance test on the selected classifier."""
 
    def test_classifier(
        self,
        classifier: Classifier,
        test_set: LearningSet,
        generalization_threshold: float = 0.15,
    ) -> TestingReport:
        print(f"[TestingOrchestrator] Testing classifier '{classifier.classifier_id}' …")
 
        # --- Stub: replace with real model inference on test_set ---
        testing_error = 0.08
        passed = testing_error <= generalization_threshold
 
        hp = HyperParameters(
            num_layers=classifier.number_of_layers,
            num_neurons=classifier.number_of_neurons,
            classifier_id=classifier.classifier_id,
        )
 
        report = TestingReport(
            classifier=hp,
            testing_error=testing_error,
            generalization_threshold=generalization_threshold,
            result=passed,
        )
        print(
            f"[TestingOrchestrator] Testing error={testing_error}, "
            f"Threshold={generalization_threshold}, Passed={passed}"
        )
        return report