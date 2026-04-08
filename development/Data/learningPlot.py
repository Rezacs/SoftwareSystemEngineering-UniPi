from dataclasses import dataclass, field
from typing import List

@dataclass
class LearningPlot:
    mse: List[float] = field(default_factory=list)
    number_of_epochs: List[int] = field(default_factory=list)
    approve: bool = False
    set_epochs: bool = False