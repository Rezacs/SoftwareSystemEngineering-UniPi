class StateManager:
    """
    Controls system batch state (continuous processing)
    """

    def __init__(self):
        self.current_batch = None

    # ================= BATCH CONTROL =================

    def set_batch(self, batch):
        self.current_batch = batch

    def get_batch(self):
        return self.current_batch

    def clear_batch(self):
        self.current_batch = None

    def is_waiting_decision(self):
        """
        True → system is waiting for human decision
        """
        return self.current_batch is not None