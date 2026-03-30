from dataclasses import dataclass, field
from typing import List

from matplotlib.pylab import double

@dataclass
class PreparedSession:
    """A single sample: a feature vector and its label."""
    UUID: str = ""
    idPlayer: str = ""
    skillOverall: double = 0.0
    socialInfluence: double = 0.0
    injuriesImpact: double = 0.0
    label: int = 0