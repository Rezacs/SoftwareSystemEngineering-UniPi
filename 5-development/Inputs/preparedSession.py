from dataclasses import dataclass, field
@dataclass
class PreparedSession:
    """Placeholder for a prepared session entry in a dataset."""
    data: dict = field(default_factory=dict)