from dataclasses import dataclass
from typing import Optional
@dataclass
class Classifier:
    classifier_id: str = ""
    number_of_neurons: int = 0
    number_of_layers: int = 0
    validation_error: float = 0.0
    training_error: float = 0.0
    model: Optional[bytes] = None          # binary model artifact