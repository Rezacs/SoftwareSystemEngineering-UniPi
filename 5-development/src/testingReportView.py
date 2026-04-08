from Data.testingReport import TestingReport

class TestingReportView:
    def display_training_report(self, report: TestingReport) -> None:
        print("[TestingReportView] Testing Report:")
        print(f"  Classifier               : {report.classifier_id}")
        print(f"  Testing error            : {report.testing_error:.4f}")
        print(f"  Generalization threshold : {report.generalization_threshold}")
        print(f"  Passed                   : {report.result}")
        # Additional details can be printed here as needed for classifier