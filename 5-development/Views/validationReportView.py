from Data.validationReport import ValidationReport
class ValidationReportView:
    def display_validation_report(self, validation_report: ValidationReport) -> None:
        print("[ValidationReportView] Displaying validation report.")
        print(f"  Selected classifier : {validation_report.selected_classifier}")
        print(f"  Approved            : {validation_report.approve}")
        candidates_info = [
            f"(id={c.classifier_id}, layers={c.num_layers}, neurons={c.num_neurons})"
            for c in validation_report.candidates
        ]
        print(f"  Candidates          : {candidates_info}")