from Data.testingReport import TestingReport
class TestingReportView:
    def display_training_report(self, testing_report: TestingReport) -> None:
        print("[TestingReportView] Displaying testing report.")
        print(f"  Testing error            : {testing_report.testing_error}")
        print(f"  Generalization threshold : {testing_report.generalization_threshold}")
        print(f"  Result (passed)          : {testing_report.result}")