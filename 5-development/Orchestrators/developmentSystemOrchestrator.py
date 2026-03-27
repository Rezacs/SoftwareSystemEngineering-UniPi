from Data.classifier import Classifier
from Data.learningPlot import LearningPlot
from Data.validationReport import ValidationReport
from Data.testingReport import TestingReport
from Inputs.hyperParameters import HyperParameters
from Inputs.learningSet import LearningSet
from Orchestrators.training_orchestrator import TrainingOrchestrator
from Orchestrators.validation_orchestrator import ValidationOrchestrator
from Orchestrators.testing_orchestrator import TestingOrchestrator
from communicationController import CommunicationController
from Views.learningPlotView import LearningPlotView
from Views.validationReportView import ValidationReportView
from Views.testingReportView import TestingReportView
from typing import List, Optional

class DevelopmentSystemOrchestrator:
 
    def __init__(
        self,
        learning_set: LearningSet,
        hyper_param_configs: List[HyperParameters],
        overfitting_threshold: float = 0.1,
        generalization_threshold: float = 0.15,
        max_outer_iterations: int = 3,
    ) -> None:
        self._learning_set = learning_set
        self._hyper_param_configs = hyper_param_configs
        self._overfitting_threshold = overfitting_threshold
        self._generalization_threshold = generalization_threshold
        self._max_outer_iterations = max_outer_iterations
 
        # Collaborators
        self._training_orchestrator = TrainingOrchestrator()
        self._validation_orchestrator = ValidationOrchestrator()
        self._testing_orchestrator = TestingOrchestrator()
        self._communication_controller = CommunicationController()
        self._learning_plot_view = LearningPlotView()
        self._validation_report_view = ValidationReportView()
        self._testing_report_view = TestingReportView()
 
    # ------------------------------------------------------------------
    def run(self) -> None:
        print("=" * 60)
        print("Development System Orchestrator: run()")
        print("=" * 60)
 
        classifier_valid = False
        outer_iteration = 0
 
        # ── Loop [Classifier Not Valid] ────────────────────────────────
        while not classifier_valid and outer_iteration < self._max_outer_iterations:
            outer_iteration += 1
            print(f"\n--- Outer iteration {outer_iteration} ---")
 
            # ── Loop [# Iterations Not Valid] ─────────────────────────
            #    Set initial parameters and generate learning plot
            initial_config = self._hyper_param_configs[0]
            self._training_orchestrator.set_parameters(
                initial_config, self._learning_set
            )
            learning_plot = self._training_orchestrator.generate_learning_plot()
            self._learning_plot_view.display_learning_plot(learning_plot)
 
            if not learning_plot.approve:
                print("[Orchestrator] Learning plot not approved; adjusting epochs …")
                # In a real system the engineer would update num_iterations here.
 
            # ── ValidationOrchestrator.checkTable ─────────────────────
            #    Inner loop: train a classifier per hyper-parameter config
            trained_classifiers: List[Classifier] = []
            for hp_config in self._hyper_param_configs:
                self._training_orchestrator.set_parameters(
                    hp_config, self._learning_set
                )
                clf = self._training_orchestrator.train_classifier()
                trained_classifiers.append(clf)
 
            validation_report = self._validation_orchestrator.check_table(
                trained_classifiers, self._overfitting_threshold
            )
            self._validation_report_view.display_validation_report(validation_report)
 
            if not validation_report.approve:
                print("[Orchestrator] Validation not approved; retrying …")
                continue  # outer loop
 
            # ── Find the selected Classifier object ───────────────────
            selected_clf = next(
                (c for c in trained_classifiers
                 if c.classifier_id == validation_report.selected_classifier),
                None,
            )
            if selected_clf is None:
                print("[Orchestrator] Selected classifier not found; retrying …")
                continue
 
            # ── TestingOrchestrator.testClassifier ────────────────────
            testing_report = self._testing_orchestrator.test_classifier(
                selected_clf,
                self._learning_set,
                self._generalization_threshold,
            )
            self._testing_report_view.display_training_report(testing_report)
 
            # ── alt [Test Passed / Test Not Passed] ───────────────────
            if testing_report.result:
                print("\n[Orchestrator] Test PASSED → sending classifier.")
                self._communication_controller.send_classifier(selected_clf)
                classifier_valid = True
            else:
                print("\n[Orchestrator] Test NOT PASSED → sending configuration.")
                best_hp = testing_report.classifier or self._hyper_param_configs[0]
                self._communication_controller.send_configuration(best_hp)
                # Loop continues to retrain
 
        if classifier_valid:
            print("\n✓ Development cycle completed successfully.")
        else:
            print(
                f"\n✗ Development cycle ended after {outer_iteration} iterations "
                "without a passing classifier."
            )