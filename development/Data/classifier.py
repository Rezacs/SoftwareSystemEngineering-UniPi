"""Data class representing a trained classifier and its performance metrics."""

from dataclasses import dataclass


@dataclass
class Classifier:
    """Holds identity, architecture, and error metrics for a trained classifier."""

    classifier_id: str
    number_of_neurons: int
    number_of_layers: int
    training_error: float
    validation_error: float
    model_path: str  # path to joblib-serialised model on disk