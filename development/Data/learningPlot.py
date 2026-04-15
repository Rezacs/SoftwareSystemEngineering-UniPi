"""Data class representing a learning curve produced during calibration."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class LearningPlot:
    """Stores per-epoch MSE values and whether the curve was approved."""

    mse: List[float] = field(default_factory=list)
    number_of_epochs: List[int] = field(default_factory=list)
    approve: bool = False
    set_epochs: bool = False