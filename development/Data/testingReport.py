"""Data class representing the outcome of the final testing phase."""

from dataclasses import dataclass


@dataclass
class TestingReport:
    """Holds the testing error, threshold, and pass/fail result for a classifier."""

    classifier_id: str
    testing_error: float
    generalization_threshold: float
    result: bool