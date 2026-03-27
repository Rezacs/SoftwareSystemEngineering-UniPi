from dataclasses import dataclass, field
from typing import List

@dataclass
class PreparedSession:
    """A single sample: a feature vector and its label."""
    features: List[float] = field(default_factory=list)
    label: int = 0