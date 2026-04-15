"""Orchestrator for the training and calibration phases of the development pipeline."""

import matplotlib
matplotlib.use("Agg")   # safe for server/thread contexts

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Optional

import joblib
from sklearn.neural_network import MLPClassifier

from Data.classifier import Classifier
from Data.learningPlot import LearningPlot
from Data.preparedSession import PreparedSession


def _sessions_to_frames(sessions: List[PreparedSession], feature_cols: List[str]):
    """Convert a list of PreparedSession objects into a feature DataFrame and label list."""
    X = pd.DataFrame(
        [{col: getattr(s, col) for col in feature_cols} for s in sessions]
    )
    y = [s.label for s in sessions]
    return X, y


def _to_numpy(X) -> np.ndarray:
    """
    Accept a DataFrame or ndarray and always return a plain ndarray.

    This ensures the MLPClassifier is never fitted or called with
    feature names, avoiding the sklearn UserWarning at prediction time.
    """
    if isinstance(X, pd.DataFrame):
        return X.values
    return np.asarray(X)


class TrainingOrchestrator:
    """Handles MLP calibration, learning-curve generation, and full training."""

    def __init__(self, feature_cols: List[str], score_min: int, score_max: int) -> None:
        """Initialise with feature column names and score range."""
        self._params:       dict      = {}
        self._feature_cols: List[str] = feature_cols
        self._score_min:    int       = score_min
        self._score_max:    int       = score_max

    # ── BPMN Task: SET HYPERPARAMS ─────────────────────────────────────

    def set_parameters(self, params: dict) -> None:
        """Store hyperparameter dict for use in subsequent training calls."""
        print(f"[TrainingOrchestrator] SET HYPERPARAMS: {params}")
        self._params = params

    def _build_mlp(self, max_iter: Optional[int] = None) -> MLPClassifier:
        """Construct an MLPClassifier from the currently stored parameters."""
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
        """Train for num_epochs, save the learning-curve plot, and return a LearningPlot."""
        print(f"[TrainingOrchestrator] CALIBRATE — {num_epochs} epochs …")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        mlp = self._build_mlp(max_iter=num_epochs)
        mlp.fit(_to_numpy(X_train), y_train)

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

    def generate_learning_curve(
        self,
        X_train: pd.DataFrame,
        y_train: list,
        output_path: str,
        num_epochs: int = 10,
    ) -> LearningPlot:
        """Alias for generate_calibration_report."""
        return self.generate_calibration_report(X_train, y_train, output_path, num_epochs)

    # ── Training ────────────────────────────────────────────────────────

    def train_classifier(
        self,
        X_train: pd.DataFrame,
        y_train: list,
        X_val: pd.DataFrame,
        y_val: list,
        classifier_id: str,
        model_path: str,
    ) -> Classifier:
        """Train the MLP, persist it to disk, and return a Classifier data object."""
        print(f"[TrainingOrchestrator] Training '{classifier_id}' …")
        model_path = Path(model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)

        x_train_np = _to_numpy(X_train)
        x_val_np   = _to_numpy(X_val)

        mlp = self._build_mlp()
        mlp.fit(x_train_np, y_train)

        training_error   = 1.0 - mlp.score(x_train_np, y_train)
        validation_error = 1.0 - mlp.score(x_val_np,   y_val)

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