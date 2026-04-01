class LearningSetsController:
    def generate_learning_sets(self, prepared_sessions: list) -> dict:
        total = len(prepared_sessions)

        if total == 0:
            return {
                "training_set": [],
                "validation_set": [],
                "test_set": []
            }

        train_end = int(total * 0.7)
        val_end = int(total * 0.85)

        return {
            "training_set": prepared_sessions[:train_end],
            "validation_set": prepared_sessions[train_end:val_end],
            "test_set": prepared_sessions[val_end:]
        }