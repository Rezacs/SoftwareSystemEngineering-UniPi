from dataclasses import dataclass

@dataclass
class TestingReport:
    classifier_id: str
    testing_error: float
    generalization_threshold: float
    result: bool