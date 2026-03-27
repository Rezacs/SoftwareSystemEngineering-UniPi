import pickle
from typing import Optional

import numpy as np

from Data.classifier import Classifier
from Data.testingReport import TestingReport
from Inputs.hyperParameters import HyperParameters
from Inputs.learningSet import LearningSet
from Inputs.preparedSession import PreparedSession


class TestingOrchestrator:
    """Runs the final acceptance test on the selected classifier."""

    def test_classifier(
        self,
        classifier: Classifier,
        learning_set: LearningSet,
        generalization_threshold: float = 0.15,
    ) -> TestingReport:
        print(
            f"[TestingOrchestrator] Testing classifier "
            f"'{classifier.classifier_id}' …"
        )

        # Deserialize the trained model
        mlp = pickle.loads(classifier.model)

        X_test = np.array(
            [s.features for s in learning_set.test_set], dtype=float
        )
        y_test = np.array(
            [s.label for s in learning_set.test_set], dtype=int
        )

        testing_error = 1.0 - mlp.score(X_test, y_test)
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
            f"[TestingOrchestrator] Testing error={testing_error:.4f}, "
            f"Threshold={generalization_threshold}, Passed={passed}"
        )
        return report