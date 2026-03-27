from dataclasses import dataclass, field
from typing import List
from Inputs.hyperParameters import HyperParameters

@dataclass
class ValidationReport:
    overfitting_threshold: float = 0.1
    candidates: List[HyperParameters] = field(default_factory=list)
    selected_classifier: str = ""
    approve: bool = False