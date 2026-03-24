from dataclasses import dataclass
from typing import List
from dataclasses import field
@dataclass
class LearningPlot:
    mse: List[float] = field(default_factory=list)
    number_of_epochs: List[int] = field(default_factory=list)
    approve: bool = False
    set_epochs: bool = False