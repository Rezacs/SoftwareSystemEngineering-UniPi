import json
from pathlib import Path

import joblib
import pandas as pd

from Data.testingReport import TestingReport


class TestingOrchestrator:
    def __init__(
        self,
        report_path: str,
        generalization_threshold: float = 0.15,
    ) -> None:
        self._report_path              = report_path
        self._generalization_threshold = generalization_threshold

    def test_classifier(
        self,
        model_path: str,
        classifier_data: dict,
        X_test: pd.DataFrame,
        y_test: list,
    ) -> TestingReport:
        clf_id = classifier_data.get("classifier_id", "?")
        print(f"[TestingOrchestrator] GENERATE TEST REPORT for '{clf_id}' …")

        mlp           = joblib.load(model_path)
        testing_error = 1.0 - mlp.score(X_test.values, y_test)
        passed        = testing_error <= self._generalization_threshold

        report_path = Path(self._report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="UTF-8") as f:
            json.dump({
                "classifier_id":            clf_id,
                "metric":                   "classification_error (1 - accuracy)",
                "testing_error":            round(testing_error, 4),
                "generalization_threshold": self._generalization_threshold,
                "errors": {"passed": passed},
            }, f, indent="\t")

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