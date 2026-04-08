from dataclasses import dataclass

@dataclass
class PreparedSession:
    """A single sample: a feature vector and its label."""
    UUID: str = ""
    idPlayer: str = ""
    skillOverall: float = 0.0
    socialInfluence: float = 0.0
    injuriesImpact: float = 0.0
    label: int = 0