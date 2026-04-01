class EvaluationController:
    def evaluate(self, label_pairs: list) -> dict:
        total_errors = 0
        max_consecutive_errors = 0
        current_consecutive_errors = 0

        for pair in label_pairs:
            is_error = pair["expert_label"] != pair["classifier_label"]

            if is_error:
                total_errors += 1
                current_consecutive_errors += 1
                max_consecutive_errors = max(
                    max_consecutive_errors,
                    current_consecutive_errors
                )
            else:
                current_consecutive_errors = 0

        return {
            "num_sessions": len(label_pairs),
            "total_errors": total_errors,
            "max_consecutive_errors": max_consecutive_errors
        }