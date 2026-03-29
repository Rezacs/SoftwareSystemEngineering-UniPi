# evaluation/models.py
from dataclasses import dataclass, field
from typing import List
from datetime import datetime
import uuid

@dataclass
class EvaluationConfiguration:
    required_label_count: int
    error_threshold_th1: int
    max_consecutive_errors_th2: int
    # Optional fields from your extended class diagram
    generalization_tolerance: float = 0.0
    evaluation_mode: str = "standard"
    is_valid: bool = True
    configured_by: str = "System"
    
    def getRequiredLabelCount(self) -> int:
        return self.required_label_count

@dataclass
class LabelPair:
    expert_label_class: int
    detector_label_class: int
    pair_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_match: bool = field(init=False)

    def __post_init__(self):
        # Automatically evaluates match when the object is created
        self.is_match = self.evaluateMatch()

    def evaluateMatch(self) -> bool:
        return self.expert_label_class == self.detector_label_class

@dataclass
class LabelBuffer:
    buffer_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pairs: List[LabelPair] = field(default_factory=list)

    def addPair(self, pair: LabelPair) -> None:
        self.pairs.append(pair)

    def clearBuffer(self) -> None:
        self.pairs.clear()

    def getCurrentSize(self) -> int:
        return len(self.pairs)

@dataclass
class EvaluationReport:
    total_labels_evaluated: int
    total_errors: int
    max_consecutive_errors: int
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    generation_timestamp: datetime = field(default_factory=datetime.now)
    is_approved: bool = False
    notes: str = ""

    def setApprovalStatus(self, is_approved: bool) -> None:
        self.is_approved = is_approved

    def addNotes(self, note: str) -> None:
        self.notes = note