import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error

from Data.testingReport import TestingReport
from Data.hyperParameters import HyperParameters

SCORE_MIN, SCORE_MAX = 1, 5


def _predict_scores(mlp, X: np.ndarray) -> np.ndarray:
    raw = mlp.predict(X)
    return np.clip(np.round(raw), SCORE_MIN, SCORE_MAX).astype(int)


class TestingOrchestrator:

    def __init__(
        self,
        report_path: str,
        generalization_threshold: float = 0.5,  # MAE threshold: avg error < 0.5 score points
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
        print(f"[TestingOrchestrator] Testing '{clf_id}' …")

        mlp           = joblib.load(model_path)
        preds         = _predict_scores(mlp, X_test.values)
        testing_error = mean_absolute_error(y_test, preds)
        passed        = testing_error <= self._generalization_threshold

        os.makedirs(os.path.dirname(self._report_path), exist_ok=True)
        with open(self._report_path, "w", encoding="UTF-8") as f:
            json.dump({
                "classifier_id":            clf_id,
                "metric":                   "MAE (rounded predictions)",
                "testing_error":            round(testing_error, 4),
                "generalization_threshold": self._generalization_threshold,
                "errors": {"passed": passed},
            }, f, indent="\t")

        print(
            f"[TestingOrchestrator] MAE={testing_error:.4f}, "
            f"threshold={self._generalization_threshold}, passed={passed}"
        )
        return TestingReport(
            classifier=HyperParameters(classifier_id=clf_id),
            testing_error=testing_error,
            generalization_threshold=self._generalization_threshold,
            result=passed,
        )