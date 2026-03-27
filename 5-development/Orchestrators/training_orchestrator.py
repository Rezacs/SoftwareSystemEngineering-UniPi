import pickle
from typing import Optional, List

import numpy as np
from sklearn.neural_network import MLPClassifier

from Data.classifier import Classifier
from Data.learningPlot import LearningPlot
from Inputs.hyperParameters import HyperParameters
from Inputs.learningSet import LearningSet
from Inputs.preparedSession import PreparedSession


def _to_arrays(sessions: List[PreparedSession]):
    """Convert a list of PreparedSession into (X, y) numpy arrays."""
    X = np.array([s.features for s in sessions], dtype=float)
    y = np.array([s.label    for s in sessions], dtype=int)
    return X, y


class TrainingOrchestrator:
    """Handles classifier training for a single hyper-parameter configuration."""

    def __init__(self) -> None:
        self._hyper_params: Optional[HyperParameters] = None
        self._learning_set: Optional[LearningSet] = None

    def set_parameters(
        self,
        hyper_params: HyperParameters,
        learning_set: LearningSet,
    ) -> None:
        print(f"[TrainingOrchestrator] Setting parameters: {hyper_params}")
        self._hyper_params = hyper_params
        self._learning_set = learning_set

    def train_classifier(self) -> Classifier:
        """Train an MLPClassifier and return a Classifier data object."""
        if self._hyper_params is None or self._learning_set is None:
            raise RuntimeError("Parameters must be set before training.")

        hp = self._hyper_params
        print(
            f"[TrainingOrchestrator] Training classifier '{hp.classifier_id}' — "
            f"layers={hp.num_layers}, neurons={hp.num_neurons}, "
            f"iterations={hp.num_iterations} …"
        )

        X_train, y_train = _to_arrays(self._learning_set.training_set)
        X_val,   y_val   = _to_arrays(self._learning_set.validation_set)

        mlp = MLPClassifier(
            hidden_layer_sizes=tuple([hp.num_neurons] * hp.num_layers),
            max_iter=hp.num_iterations,
            random_state=42,
        )
        mlp.fit(X_train, y_train)

        training_error   = 1.0 - mlp.score(X_train, y_train)
        validation_error = 1.0 - mlp.score(X_val,   y_val)

        model_bytes = pickle.dumps(mlp)

        classifier = Classifier(
            classifier_id=hp.classifier_id,
            number_of_neurons=hp.num_neurons,
            number_of_layers=hp.num_layers,
            training_error=training_error,
            validation_error=validation_error,
            model=model_bytes,
        )
        print(
            f"[TrainingOrchestrator] Done. "
            f"Training error={training_error:.4f}, "
            f"Validation error={validation_error:.4f}"
        )
        return classifier

    def generate_learning_plot(self, num_epochs: int = 10) -> LearningPlot:
        """
        Train a short run to capture loss_curve_, then return a LearningPlot.
        Uses the current hyper-params and learning set.
        """
        if self._hyper_params is None or self._learning_set is None:
            raise RuntimeError("Parameters must be set before generating a plot.")

        hp = self._hyper_params
        print("[TrainingOrchestrator] Generating learning plot …")

        X_train, y_train = _to_arrays(self._learning_set.training_set)

        mlp = MLPClassifier(
            hidden_layer_sizes=tuple([hp.num_neurons] * hp.num_layers),
            max_iter=num_epochs,
            random_state=42,
            warm_start=False,
        )
        mlp.fit(X_train, y_train)

        # loss_curve_ contains one loss value per epoch actually run
        mse    = mlp.loss_curve_
        epochs = list(range(1, len(mse) + 1))

        # Auto-approve if the loss is still falling at the end
        approve = len(mse) >= 2 and mse[-1] < mse[0]

        return LearningPlot(
            mse=mse,
            number_of_epochs=epochs,
            approve=approve,
            set_epochs=False,
        )