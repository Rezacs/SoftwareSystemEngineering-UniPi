from Data.validationReport import ValidationReport

class ValidationReportView:
    def display_validation_report(self, report: ValidationReport) -> None:
        print("[ValidationReportView] Validation Report:")
        print(f"  Overfitting threshold : {report.overfitting_threshold}")
        print(f"  Candidates            : {len(report.candidates)}")
        print(f"  Selected classifier   : '{report.selected_classifier}'")
        print(f"  Approved              : {report.approve}")