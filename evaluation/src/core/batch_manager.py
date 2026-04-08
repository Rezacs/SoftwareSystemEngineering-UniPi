class BatchManager:
    """
    Handles batch readiness and selection
    """

    def __init__(self, batch_size):
        self.batch_size = batch_size

    def is_ready(self, matched_pairs):
        return len(matched_pairs) >= self.batch_size

    def get_batch(self, matched_pairs):

        if not self.is_ready(matched_pairs):
            return None

        # enforce deterministic ordering
        matched_pairs = sorted(matched_pairs, key=lambda x: x["player_id"])

        return matched_pairs[:self.batch_size]