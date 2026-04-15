"""View component for displaying a validation report to the console."""

from Data.validationReport import ValidationReport


class ValidationReportView:
    """Renders a ValidationReport object as formatted console output."""

    def display_validation_report(self, report: ValidationReport) -> None:
        """Print the validation results including the selected classifier."""
        print("[ValidationReportView] Validation Report:")
        print(f"  Overfitting threshold : {report.overfitting_threshold}")
        print(f"  Candidates            : {len(report.candidates)}")
        print(f"  Selected classifier   : '{report.selected_classifier}'")
        print(f"  Approved              : {report.approve}")