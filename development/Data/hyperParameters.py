"""Data class for neural-network hyperparameter configuration."""

from dataclasses import dataclass


@dataclass
# Just for testing
class HyperParameters:
    """Stores the hyperparameter settings for a single classifier configuration."""

    num_layers: int = 1
    num_neurons: int = 32
    num_iterations: int = 200
    classifier_id: str = ""