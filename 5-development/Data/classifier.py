from dataclasses import dataclass

@dataclass
class Classifier:
    classifier_id: str
    number_of_neurons: int
    number_of_layers: int
    training_error: float
    validation_error: float
    model: bytes  # pickle-serialized sklearn model