from dataclasses import dataclass
from typing import Optional
from Data.hyperParameters import HyperParameters

@dataclass
class TestingReport:
    classifier: Optional[HyperParameters]
    testing_error: float
    generalization_threshold: float
    result: bool