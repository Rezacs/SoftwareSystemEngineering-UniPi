from dataclasses import dataclass
from Inputs.hyperParameters import HyperParameters
from typing import Optional
@dataclass
class TestingReport:
    classifier: Optional[HyperParameters] = None
    testing_error: float = 0.0
    generalization_threshold: float = 0.0
    result: bool = False