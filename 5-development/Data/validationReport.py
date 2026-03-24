from Inputs.hyperParameters import HyperParameters
from dataclasses import dataclass, field
from typing import List
@dataclass
class ValidationReport:
    overfitting_threshold: float = 0.0
    candidates: List[HyperParameters] = field(default_factory=list)
    selected_classifier: str = ""
    approve: bool = False