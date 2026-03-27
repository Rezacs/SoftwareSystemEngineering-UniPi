from dataclasses import dataclass
from typing import Optional
from Inputs.hyperParameters import HyperParameters

@dataclass
class TestingReport:
    classifier: Optional[HyperParameters]
    testing_error: float
    generalization_threshold: float
    result: bool