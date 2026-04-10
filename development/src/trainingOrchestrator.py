from pathlib import Path
from typing import List, Optional

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score

from Data.classifier import Classifier
from Data.learningPlot import LearningPlot
from Data.preparedSession import PreparedSession


def _sessions_to_frames(sessions: List[PreparedSession], feature_cols: List[str]):
    X = pd.DataFrame(
        [{col: getattr(s, col) for col in feature_cols} for s in sessions]
    )
    y = [s.label for s in sessions]
    return X, y


class TrainingOrchestrator:

    def __init__(self, feature_cols: List[str], score_min: int, score_max: int) -> None:
        self._params:       dict      = {}
        self._feature_cols: List[str] = feature_cols
        self._score_min:    int       = score_min
        self._score_max:    int       = score_max

    # ── BPMN Task: SET HYPERPARAMS ─────────────────────────────────────

    def set_parameters(self, params: dict) -> None:
        """BPMN Task: SET HYPERPARAMS"""
        print(f"[TrainingOrchestrator] SET HYPERPARAMS: {params}")
        self._params = params

    def _build_mlp(self, max_iter: Optional[int] = None) -> MLPClassifier:
        num_layers  = self._params.get("num_layers",  2)
        num_neurons = self._params.get("num_neurons", 64)
        iterations  = max_iter or self._params.get("max_iter", 200)
        return MLPClassifier(
            hidden_layer_sizes=tuple([num_neurons] * num_layers),
            max_iter=iterations,
            random_state=42,
        )

    # ── BPMN Tasks: CALIBRATE + GENERATE CALIBRATION REPORT ───────────

    def generate_calibration_report(
        self,
        X_train: pd.DataFrame,
        y_train: list,
        output_path: str,
        num_epochs: int = 10,
    ) -> LearningPlot:
        """
        BPMN Tasks: CALIBRATE & GENERATE CALIBRATION REPORT.
        Fits the MLP for num_epochs iterations, saves the loss curve
        as a PNG, and returns a LearningPlot for the view layer.
        """
        print(f"[TrainingOrchestrator] CALIBRATE — {num_epochs} epochs …")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        mlp = self._build_mlp(max_iter=num_epochs)
        mlp.fit(X_train.values, y_train)

        mse    = mlp.loss_curve_
        epochs = list(range(1, len(mse) + 1))

        plt.figure()
        plt.plot(epochs, mse, marker="o")
        plt.xlabel("Epoch")
        plt.ylabel("Loss")
        plt.title("Calibration Report — Learning Curve")
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        print(f"[TrainingOrchestrator] GENERATE CALIBRATION REPORT → {output_path}")

        approve = len(mse) >= 2 and mse[-1] < mse[0]
        return LearningPlot(mse=mse, number_of_epochs=epochs, approve=approve, set_epochs=False)

    # alias
    def generate_learning_curve(self, X_train, y_train, output_path, num_epochs=10):
        return self.generate_calibration_report(X_train, y_train, output_path, num_epochs)

    # ── Training (called per HP config inside grid search) ─────────────

    def train_classifier(
        self,
        X_train: pd.DataFrame,
        y_train: list,
        X_val: pd.DataFrame,
        y_val: list,
        classifier_id: str,
        model_path: str,
    ) -> Classifier:
        """
        Trains one MLPClassifier with the currently set hyper-parameters.
        Error metric: classification error (1 - accuracy) on integer scores {1..5}.
        Persists the model to disk with joblib.
        """
        print(f"[TrainingOrchestrator] Training '{classifier_id}' …")
        model_path = Path(model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)

        mlp = self._build_mlp()
        mlp.fit(X_train.values, y_train)

        training_error   = 1.0 - mlp.score(X_train.values, y_train)
        validation_error = 1.0 - mlp.score(X_val.values,   y_val)

        joblib.dump(mlp, model_path)

        print(
            f"[TrainingOrchestrator] '{classifier_id}' — "
            f"train_err={training_error:.4f}, val_err={validation_error:.4f}"
        )
        return Classifier(
            classifier_id=classifier_id,
            number_of_neurons=self._params.get("num_neurons", 64),
            number_of_layers=self._params.get("num_layers",  2),
            training_error=training_error,
            validation_error=validation_error,
            model_path=model_path,
        )