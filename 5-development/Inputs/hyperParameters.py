from dataclasses import dataclass

@dataclass
#Just for testing
class HyperParameters:
    num_layers: int = 1
    num_neurons: int = 32
    num_iterations: int = 200
    classifier_id: str = ""