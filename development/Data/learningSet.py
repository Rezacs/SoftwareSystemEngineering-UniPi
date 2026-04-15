"""Data class grouping the three dataset splits used during development."""

from dataclasses import dataclass, field
from typing import List

from .preparedSession import PreparedSession


@dataclass
class LearningSet:
    """Container for training, validation, and test session lists."""

    training_set: List[PreparedSession] = field(default_factory=list)
    validation_set: List[PreparedSession] = field(default_factory=list)
    test_set: List[PreparedSession] = field(default_factory=list)