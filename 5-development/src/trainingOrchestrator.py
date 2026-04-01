import os
from typing import List, Optional

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_error

from Data.classifier import Classifier
from Data.learningPlot import LearningPlot
from Data.preparedSession import PreparedSession
from src.config import FEATURE_COLS, SCORE_MIN, SCORE_MAX


def _sessions_to_frames(sessions: List[PreparedSession]):
    X = pd.DataFrame(
        [{col: getattr(s, col) for col in FEATURE_COLS} for s in sessions]
    )
    y = [s.label for s in sessions]
    return X, y


def _predict_scores(mlp: MLPRegressor, X: np.ndarray) -> np.ndarray:
    """Clip and round raw float predictions to the nearest integer in [SCORE_MIN, SCORE_MAX]."""
    return np.clip(np.round(mlp.predict(X)), SCORE_MIN, SCORE_MAX).astype(int)


class TrainingOrchestrator:
    """
    Implements the BPMN tasks:
      • SET HYPERPARAMS (configuration)  → set_parameters()
      • CALIBRATE                        → generate_calibration_report()
      • GENERATE CALIBRATION REPORT      → generate_calibration_report()
      • train_classifier()               → called per HP config inside grid search
    """

    def __init__(self) -> None:
        self._params: dict = {}

    # ── BPMN Task: SET HYPERPARAMS ─────────────────────────────────────

    def set_parameters(self, params: dict) -> None:
        """
        BPMN Task: SET HYPERPARAMS
        Receives the hyper-parameter dict before training or calibration.
        """
        print(f"[TrainingOrchestrator] SET HYPERPARAMS: {params}")
        self._params = params

    def _build_mlp(self, max_iter: Optional[int] = None) -> MLPRegressor:
        num_layers  = self._params.get("num_layers",  2)
        num_neurons = self._params.get("num_neurons", 64)
        iterations  = max_iter or self._params.get("max_iter", 200)
        return MLPRegressor(
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
        Fits the MLP for num_epochs, saves the loss curve as a PNG,
        and returns a LearningPlot for the view layer.
        """
        print(f"[TrainingOrchestrator] CALIBRATE — {num_epochs} epochs …")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        mlp = self._build_mlp(max_iter=num_epochs)
        mlp.fit(X_train.values, y_train)

        mse    = mlp.loss_curve_
        epochs = list(range(1, len(mse) + 1))

        plt.figure()
        plt.plot(epochs, mse, marker="o")
        plt.xlabel("Epoch")
        plt.ylabel("MSE Loss")
        plt.title("Calibration Report — Learning Curve")
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        print(f"[TrainingOrchestrator] GENERATE CALIBRATION REPORT → {output_path}")

        approve = len(mse) >= 2 and mse[-1] < mse[0]
        return LearningPlot(mse=mse, number_of_epochs=epochs, approve=approve, set_epochs=False)

    # alias for backward compatibility
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
        Trains one MLPRegressor, computes MAE on train and validation sets,
        and persists the model to disk with joblib.
        """
        print(f"[TrainingOrchestrator] Training '{classifier_id}' …")
        os.makedirs(os.path.dirname(model_path), exist_ok=True)

        mlp = self._build_mlp()
        mlp.fit(X_train.values, y_train)

        train_preds = _predict_scores(mlp, X_train.values)
        val_preds   = _predict_scores(mlp, X_val.values)

        training_error   = mean_absolute_error(y_train, train_preds)
        validation_error = mean_absolute_error(y_val,   val_preds)

        joblib.dump(mlp, model_path)

        print(
            f"[TrainingOrchestrator] '{classifier_id}' — "
            f"train_MAE={training_error:.4f}, val_MAE={validation_error:.4f}"
        )
        return Classifier(
            classifier_id=classifier_id,
            number_of_neurons=self._params.get("num_neurons", 64),
            number_of_layers=self._params.get("num_layers",  2),
            training_error=training_error,
            validation_error=validation_error,
            model_path=model_path,
        )