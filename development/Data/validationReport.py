"""Data class representing the outcome of the validation phase."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ValidationReport:
    """Stores overfitting analysis results and the selected classifier."""

    overfitting_threshold: float = 0.1
    candidates: List[str] = field(default_factory=list)
    selected_classifier: str = ""
    approve: bool = False