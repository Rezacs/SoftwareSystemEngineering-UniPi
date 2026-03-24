from Data.classifier import Classifier
from Data.validationReport import ValidationReport
from Inputs.hyperParameters import HyperParameters
from typing import List, Optional
class ValidationOrchestrator:
    """Evaluates a set of trained classifiers and selects the best one."""
 
    def check_table(
        self,
        classifiers: List[Classifier],
        overfitting_threshold: float = 0.1,
    ) -> ValidationReport:
        print("[ValidationOrchestrator] Checking classifier table …")
 
        candidates: List[HyperParameters] = []
        best: Optional[Classifier] = None
 
        for clf in classifiers:
            overfit_gap = clf.validation_error - clf.training_error
            if overfit_gap <= overfitting_threshold:
                hp = HyperParameters(
                    num_layers=clf.number_of_layers,
                    num_neurons=clf.number_of_neurons,
                    classifier_id=clf.classifier_id,
                )
                candidates.append(hp)
                if best is None or clf.validation_error < best.validation_error:
                    best = clf
 
        selected_id = best.classifier_id if best else ""
        approved = best is not None
        report = ValidationReport(
            overfitting_threshold=overfitting_threshold,
            candidates=candidates,
            selected_classifier=selected_id,
            approve=approved,
        )
        print(
            f"[ValidationOrchestrator] Selected: '{selected_id}', "
            f"Approved: {approved}, Candidates: {len(candidates)}"
        )
        return report