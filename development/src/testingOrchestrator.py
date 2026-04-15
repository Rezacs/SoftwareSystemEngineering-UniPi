"""Orchestrator for the final testing phase of the development pipeline."""

import json
from pathlib import Path

import joblib
import pandas as pd

from Data.testingReport import TestingReport


class TestingOrchestrator:
    """Evaluates a trained classifier on the held-out test set."""

    def __init__(
        self,
        report_path: str,
        generalization_threshold: float = 0.15,
    ) -> None:
        """Store the report output path and acceptance threshold."""
        self._report_path              = report_path
        self._generalization_threshold = generalization_threshold

    def test_classifier(
        self,
        model_path: str,
        classifier_data: dict,
        X_test: pd.DataFrame,
        y_test: list,
    ) -> TestingReport:
        """Load the classifier, compute test error, write report, and return result."""
        clf_id = classifier_data.get("classifier_id", "?")
        print(f"[TestingOrchestrator] GENERATE TEST REPORT for '{clf_id}' …")

        mlp           = joblib.load(model_path)
        testing_error = 1.0 - mlp.score(X_test.values, y_test)
        passed        = testing_error <= self._generalization_threshold

        report_path = Path(self._report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="UTF-8") as fh:
            json.dump({
                "classifier_id":            clf_id,
                "metric":                   "classification_error (1 - accuracy)",
                "testing_error":            round(testing_error, 4),
                "generalization_threshold": self._generalization_threshold,
                "errors": {"passed": passed},
            }, fh, indent="\t")

        print(
            f"[TestingOrchestrator] error={testing_error:.4f}, "
            f"threshold={self._generalization_threshold}, passed={passed}"
        )
        return TestingReport(
            classifier_id=clf_id,
            testing_error=testing_error,
            generalization_threshold=self._generalization_threshold,
            result=passed,
        )