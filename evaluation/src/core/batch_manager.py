"""Batch management utilities for evaluation processing."""
class BatchManager:
    """
    Handles batch readiness and selection
    """

    def __init__(self, batch_size):
        self.batch_size = batch_size

    def is_ready(self, matched_pairs):
        """Return True if enough matched pairs exist to form a batch."""
        return len(matched_pairs) >= self.batch_size

    def get_batch(self, matched_pairs):
        """Return a deterministic batch of matched pairs if enough data exists."""
        if not self.is_ready(matched_pairs):
            return None

        # enforce deterministic ordering
        matched_pairs = sorted(matched_pairs, key=lambda x: x["player_id"])

        return matched_pairs[:self.batch_size]
    