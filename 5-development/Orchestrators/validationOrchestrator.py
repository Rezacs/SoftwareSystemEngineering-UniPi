import json
import os
from typing import List, Optional

import pandas as pd

from Data.classifier import Classifier
from Data.validationReport import ValidationReport
from Inputs.hyperParameters import HyperParameters
from Orchestrators.trainingOrchestrator import TrainingOrchestrator


class ValidationOrchestrator:

    def __init__(
        self,
        hp_configs: List[HyperParameters],
        classifier_folder: str,
        report_path: str,
        training_orchestrator: TrainingOrchestrator,
        overfitting_threshold: float = 0.1,
    ) -> None:
        self._hp_configs            = hp_configs
        self._classifier_folder     = classifier_folder
        self._report_path           = report_path
        self._training_orchestrator = training_orchestrator
        self._overfitting_threshold = overfitting_threshold

    def retrieve_average_parameters(self) -> dict:
        avg_layers  = sum(h.num_layers  for h in self._hp_configs) / len(self._hp_configs)
        avg_neurons = sum(h.num_neurons for h in self._hp_configs) / len(self._hp_configs)
        return {
            "num_layers":  int(round(avg_layers)),
            "num_neurons": int(round(avg_neurons)),
        }

    def grid_search(
        self,
        X_train: pd.DataFrame,
        y_train: list,
        X_val: pd.DataFrame,
        y_val: list,
    ) -> ValidationReport:
        print("[ValidationOrchestrator] Starting grid search …")
        classifiers: List[Classifier] = []

        for idx, hp in enumerate(self._hp_configs, start=1):
            model_path = os.path.join(self._classifier_folder, f"model_{idx}.sav")
            self._training_orchestrator.set_parameters({
                "num_layers":  hp.num_layers,
                "num_neurons": hp.num_neurons,
                "max_iter":    hp.num_iterations,
            })
            clf = self._training_orchestrator.train_classifier(
                X_train, y_train, X_val, y_val,
                classifier_id=hp.classifier_id,
                model_path=model_path,
            )
            classifiers.append(clf)

        candidates: List[dict] = []
        best: Optional[Classifier] = None

        for idx, clf in enumerate(classifiers, start=1):
            gap   = clf.validation_error - clf.training_error
            valid = gap <= self._overfitting_threshold
            candidates.append({
                "index":            idx,
                "classifier_id":    clf.classifier_id,
                "training_error":   round(clf.training_error,   4),
                "validation_error": round(clf.validation_error, 4),
                "overfitting_gap":  round(gap, 4),
                "valid":            valid,
            })
            if valid and (best is None or clf.validation_error < best.validation_error):
                best = clf

        selected_id = best.classifier_id if best else ""
        approved    = best is not None

        os.makedirs(os.path.dirname(self._report_path), exist_ok=True)
        with open(self._report_path, "w", encoding="UTF-8") as f:
            json.dump({
                "overfitting_threshold": self._overfitting_threshold,
                "best_classifiers":      candidates,
                "selected_classifier":   selected_id,
                "approve":               approved,
            }, f, indent="\t")

        print(
            f"[ValidationOrchestrator] Selected='{selected_id}', "
            f"Approved={approved}, Candidates={len(candidates)}"
        )
        return ValidationReport(
            overfitting_threshold=self._overfitting_threshold,
            candidates=[
                HyperParameters(classifier_id=c["classifier_id"])
                for c in candidates if c["valid"]
            ],
            selected_classifier=selected_id,
            approve=approved,
        )