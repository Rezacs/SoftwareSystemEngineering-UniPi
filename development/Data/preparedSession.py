"""Data class representing a single prepared player session sample."""

from dataclasses import dataclass


@dataclass
class PreparedSession:
    """A single sample: a feature vector and its label."""

    UUID: str = ""
    player_id: str = ""
    skill_overall: float = 0.0
    social_influence: float = 0.0
    injuries_impact: float = 0.0
    label: int = 0