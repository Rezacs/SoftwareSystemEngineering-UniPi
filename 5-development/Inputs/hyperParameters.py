from dataclasses import dataclass
@dataclass
class HyperParameters:
    num_layers: int = 0
    num_neurons: int = 0
    num_iterations: int = 0
    classifier_id: str = ""