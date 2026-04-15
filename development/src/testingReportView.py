"""View component for displaying a testing report to the console."""

from Data.testingReport import TestingReport


class TestingReportView:
    """Renders a TestingReport object as formatted console output."""

    def display_training_report(self, report: TestingReport) -> None:
        """Print the classifier testing results."""
        print("[TestingReportView] Testing Report:")
        print(f"  Classifier               : {report.classifier_id}")
        print(f"  Testing error            : {report.testing_error:.4f}")
        print(f"  Generalization threshold : {report.generalization_threshold}")
        print(f"  Passed                   : {report.result}")