# evaluation/report_generator.py
from evaluation.models import LabelPair, EvaluationConfiguration, EvaluationReport

class ReportGenerator:
    
    def generateEvaluationReport(self, pairs: list, config: EvaluationConfiguration) -> EvaluationReport:
        """Calculates errors and returns a fresh EvaluationReport entity."""
        total_errors = self._calculateTotalErrors(pairs)
        max_consecutive = self._calculateConsecutiveErrors(pairs)

        # Create the new Report Entity
        return EvaluationReport(
            total_labels_evaluated=len(pairs),
            total_errors=total_errors,
            max_consecutive_errors=max_consecutive
        )

    def _calculateTotalErrors(self, pairs: list) -> int:
        # Sums up all pairs where is_match is False
        return sum(1 for pair in pairs if not pair.is_match)

    def _calculateConsecutiveErrors(self, pairs: list) -> int:
        max_consecutive_errors = 0
        current_consecutive_errors = 0

        for pair in pairs:
            if not pair.is_match:
                current_consecutive_errors += 1
                max_consecutive_errors = max(
                    max_consecutive_errors,
                    current_consecutive_errors
                )
            else:
                current_consecutive_errors = 0

        return max_consecutive_errors