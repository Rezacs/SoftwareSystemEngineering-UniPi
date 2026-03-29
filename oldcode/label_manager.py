# evaluation/label_manager.py
from models import LabelPair, LabelBuffer
from common.json_io import JsonIO

class LabelManager:
    def __init__(self, buffer_path: str = "data/outputs/evaluation_buffer.json"):
        self.buffer = LabelBuffer()
        self.buffer_path = buffer_path

    def parse_incoming_json(self, json_payload: dict) -> LabelPair:
        """Acts like your old label_controller to build a pair from raw JSON."""
        # Note: Using your old logic where expert/classifier labels were both 'predicted_stars'
        expert_stars = json_payload.get("expert_label", json_payload.get("predicted_stars", 0))
        classifier_stars = json_payload.get("classifier_label", json_payload.get("predicted_stars", 0))
        
        return LabelPair(
            expert_label_class=expert_stars,
            detector_label_class=classifier_stars
        )

    def storeLabel(self, label_pair: LabelPair) -> None:
        """Adds to the buffer and saves state using JsonIO."""
        self.buffer.addPair(label_pair)
        self._save_state()

    def checkSufficientLabels(self, required_count: int) -> bool:
        return self.buffer.getCurrentSize() >= required_count

    def removeLabels(self) -> None:
        """Clears the buffer and updates the saved state."""
        self.buffer.clearBuffer()
        self._save_state()

    def getMatchedPairs(self) -> list:
        return self.buffer.pairs

    def _save_state(self) -> None:
        """Helper to keep your JSON file in sync with the live buffer object."""
        # Convert objects back to dicts for JsonIO
        data = [
            {
                "expert_label": p.expert_label_class, 
                "classifier_label": p.detector_label_class, 
                "is_match": p.is_match
            } for p in self.buffer.pairs
        ]
        JsonIO.save(self.buffer_path, data)