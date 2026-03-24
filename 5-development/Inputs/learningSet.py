from dataclasses import dataclass, field
from typing import List
import preparedSession
@dataclass

class LearningSet:
    training_set: List[preparedSession.PreparedSession] = field(default_factory=list)
    validation_set: List[preparedSession.PreparedSession] = field(default_factory=list)
    test_set: List[preparedSession.PreparedSession] = field(default_factory=list)