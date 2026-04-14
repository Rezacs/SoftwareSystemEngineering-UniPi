import threading


class StateManager:
    """
    Controls system batch state (continuous processing)
    """

    def __init__(self):
        self.current_batch = None
        self.current_session_key = None
        self._lock = threading.Lock()

    # ================= BATCH CONTROL =================

    def set_batch(self, batch, session_key=None):
        with self._lock:
            self.current_batch = batch
            self.current_session_key = session_key

    def get_batch(self):
        with self._lock:
            return self.current_batch

    def get_session_key(self):
        with self._lock:
            return self.current_session_key

    def clear_batch(self):
        with self._lock:
            self.current_batch = None
            self.current_session_key = None

    def is_waiting_decision(self):
        """
        True → system is waiting for human decision
        """
        with self._lock:
            return self.current_batch is not None