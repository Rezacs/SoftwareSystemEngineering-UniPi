"""Bridge module that exposes SegregationSystemOrchestrator from 4-segregation/src."""

from pathlib import Path
import sys


SEGREGATION_ROOT = Path(__file__).resolve().parent / "4-segregation"
if str(SEGREGATION_ROOT) not in sys.path:
    sys.path.insert(0, str(SEGREGATION_ROOT))

from src.orchestrator import SegregationSystemOrchestrator
