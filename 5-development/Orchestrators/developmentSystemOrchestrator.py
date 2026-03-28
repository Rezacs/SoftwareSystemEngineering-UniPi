import json
import os
import sys
from typing import Any, Dict, List, Optional

import joblib
import pandas as pd

from Data.learningPlot import LearningPlot
from Data.validationReport import ValidationReport
from Data.testingReport import TestingReport
from Inputs.hyperParameters import HyperParameters
from Inputs.learningSet import LearningSet
from Inputs.preparedSession import PreparedSession
from Orchestrators.trainingOrchestrator import TrainingOrchestrator
from Orchestrators.validationOrchestrator import ValidationOrchestrator
from Orchestrators.testingOrchestrator import TestingOrchestrator
from Views.learningPlotView import LearningPlotView
from Views.validationReportView import ValidationReportView
from Views.testingReportView import TestingReportView

# ── Paths ──────────────────────────────────────────────────────────────
DATA_FOLDER            = "data"
STATUS_FILE_PATH       = os.path.join(DATA_FOLDER, "internal/status.json")
CLASSIFIER_FOLDER      = os.path.join(DATA_FOLDER, "classifiers/")
LEARNING_CURVE_PATH    = os.path.join(DATA_FOLDER, "reports/learning_curve.png")
VALIDATION_REPORT_PATH = os.path.join(DATA_FOLDER, "reports/validation_report.json")
TESTING_REPORT_PATH    = os.path.join(DATA_FOLDER, "reports/testing_report.json")
USER_INPUT_PATH        = os.path.join(DATA_FOLDER, "configs/user_input.json")


def _sessions_to_frames(sessions: List[PreparedSession]):
    X = pd.DataFrame([s.features for s in sessions])
    y = [s.label for s in sessions]
    return X, y


class DevelopmentSystemOrchestrator:
    """
    State-machine orchestrator for the full development cycle.

    Phases (stored in data/internal/status.json):
        Ready → LearningCurve → Validation → ValidationReport → Testing → Results
    """

    def __init__(
        self,
        learning_set: LearningSet,
        hyper_param_configs: List[HyperParameters],
        overfitting_threshold: float = 0.1,
        generalization_threshold: float = 0.15,
        max_outer_iterations: int = 3,
        testing_mode: bool = True,
    ) -> None:
        self._learning_set             = learning_set
        self._hyper_param_configs      = hyper_param_configs
        self._overfitting_threshold    = overfitting_threshold
        self._generalization_threshold = generalization_threshold
        self._max_outer_iterations     = max_outer_iterations
        self._testing_mode             = testing_mode

        # Persisted state
        self._status: Dict[str, Any] = self._load_status()

        # Views
        self._learning_plot_view     = LearningPlotView()
        self._validation_report_view = ValidationReportView()
        self._testing_report_view    = TestingReportView()

    # ── status persistence ─────────────────────────────────────────────
    def _default_status(self) -> Dict[str, Any]:
        return {
            "phase":                "Ready",
            "max_iter":             200,
            "avg_params":           {},
            "best_classifier_data": None,
            "iteration":            0,
        }

    def _load_status(self) -> Dict[str, Any]:
        if os.path.isfile(STATUS_FILE_PATH):
            with open(STATUS_FILE_PATH, "r", encoding="UTF-8") as f:
                return json.load(f)
        return self._default_status()

    def _save_status(self) -> None:
        os.makedirs(os.path.dirname(STATUS_FILE_PATH), exist_ok=True)
        with open(STATUS_FILE_PATH, "w", encoding="UTF-8") as f:
            json.dump(self._status, f, indent="\t")

    def _update_status(self, updates: Dict[str, Any]) -> None:
        self._status.update(updates)
        self._save_status()

    def _reset_status(self) -> None:
        self._status = self._default_status()
        self._save_status()

    # ── user input ─────────────────────────────────────────────────────
    def _reset_user_input(self) -> None:
        payload = {
            "max_iter":      self._status.get("max_iter", 200),
            "good_max_iter": self._status["phase"] not in ["Ready", "LearningCurve"],
            "best_model":    (self._status.get("best_classifier_data") or {}).get("index", 0),
            "approved":      False,
        }
        os.makedirs(os.path.dirname(USER_INPUT_PATH), exist_ok=True)
        with open(USER_INPUT_PATH, "w", encoding="UTF-8") as f:
            json.dump(payload, f, indent="\t")

    def _get_user_input(self) -> dict:
        if self._testing_mode:
            return self._simulate_user_input()
        try:
            with open(USER_INPUT_PATH, "r", encoding="UTF-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"ERROR: {USER_INPUT_PATH} not found.")
            sys.exit(1)

    def _simulate_user_input(self) -> dict:
        phase = self._status["phase"]
        if phase == "LearningCurve":
            return {"max_iter": 300, "good_max_iter": True}
        elif phase == "ValidationReport":
            with open(VALIDATION_REPORT_PATH, "r", encoding="UTF-8") as f:
                report = json.load(f)
            index = next(
                (item["index"] for item in report["best_classifiers"] if item["valid"]), 0
            )
            return {"best_model": index}
        elif phase == "Results":
            with open(TESTING_REPORT_PATH, "r", encoding="UTF-8") as f:
                report = json.load(f)
            return {"approved": report["errors"]["passed"]}
        return {}

    # ── helpers ────────────────────────────────────────────────────────
    def _get_frames(self, split: str):
        sessions = getattr(self._learning_set, split)
        return _sessions_to_frames(sessions)

    def _retrieve_classifier_data(self, model_index: int) -> Optional[dict]:
        with open(VALIDATION_REPORT_PATH, "r", encoding="UTF-8") as f:
            report = json.load(f)
        entry = next(
            (item for item in report["best_classifiers"] if item["index"] == model_index), None
        )
        return entry if (entry and entry["valid"]) else None

    # ── state machine entry point ──────────────────────────────────────
    def run(self) -> None:
        print("=" * 60)
        print("DevelopmentSystemOrchestrator: run()")
        print("=" * 60)
        self._update_status({"phase": "Ready"})
        self._execute_development()

    def _execute_development(self) -> None:
        phase = self._status["phase"]
        dispatch = {
            "Ready":            self._ready_phase,
            "LearningCurve":    self._learning_curve_phase,
            "Validation":       self._grid_search_phase,
            "ValidationReport": self._model_selection_phase,
            "Testing":          self._testing_phase,
            "Results":          self._results_phase,
        }
        handler = dispatch.get(phase)
        if handler:
            handler()
        else:
            print(f"[Orchestrator] Unknown phase: {phase}")

    # ── phases ─────────────────────────────────────────────────────────
    def _ready_phase(self) -> None:
        val_orch   = ValidationOrchestrator(
            hp_configs=self._hyper_param_configs,
            classifier_folder=CLASSIFIER_FOLDER,
            report_path=VALIDATION_REPORT_PATH,
            training_orchestrator=TrainingOrchestrator(),
            overfitting_threshold=self._overfitting_threshold,
        )
        avg_params = val_orch.retrieve_average_parameters()
        print(f"[Orchestrator] Average hyper-parameters: {avg_params}")

        self._update_status({"avg_params": avg_params, "phase": "LearningCurve"})

        if not self._testing_mode:
            self._reset_user_input()
            print(f"Set max_iter in {USER_INPUT_PATH}, then re-run.")
            sys.exit(0)
        else:
            self._execute_development()

    def _learning_curve_phase(self) -> None:
        user_input  = self._get_user_input()
        first_iter  = self._status.get("iteration", 0) == 0
        good_iter   = user_input.get("good_max_iter", False)

        if first_iter or not good_iter:
            self._update_status({"max_iter": user_input["max_iter"]})
            print(f"[Orchestrator] Generating learning curve "
                  f"({user_input['max_iter']} epochs) …")

            X_train, y_train = self._get_frames("training_set")
            to = TrainingOrchestrator()
            params = dict(self._status.get("avg_params", {}))
            params["max_iter"] = self._status["max_iter"]
            to.set_parameters(params)

            plot = to.generate_learning_curve(X_train, y_train, LEARNING_CURVE_PATH)
            self._learning_plot_view.display_learning_plot(plot)

            if not self._testing_mode:
                self._reset_user_input()
                print(f"Check learning curve at {LEARNING_CURVE_PATH}")
                print(f"Set good_max_iter=true in {USER_INPUT_PATH} when satisfied.")
                sys.exit(0)
            else:
                self._execute_development()
        else:
            print(f"[Orchestrator] Iterations approved: {self._status['max_iter']}")
            self._update_status({"phase": "Validation"})
            self._execute_development()

    def _grid_search_phase(self) -> None:
        print("[Orchestrator] Starting grid search …")
        X_train, y_train = self._get_frames("training_set")
        X_val,   y_val   = self._get_frames("validation_set")

        to = TrainingOrchestrator()
        to.set_parameters({"max_iter": self._status["max_iter"]})

        val_orch = ValidationOrchestrator(
            hp_configs=self._hyper_param_configs,
            classifier_folder=CLASSIFIER_FOLDER,
            report_path=VALIDATION_REPORT_PATH,
            training_orchestrator=to,
            overfitting_threshold=self._overfitting_threshold,
        )
        report = val_orch.grid_search(X_train, y_train, X_val, y_val)
        self._validation_report_view.display_validation_report(report)

        self._update_status({"phase": "ValidationReport"})

        if not self._testing_mode:
            self._reset_user_input()
            print(f"Check validation report at {VALIDATION_REPORT_PATH}")
            print(f"Set best_model in {USER_INPUT_PATH}. Use 0 to reject all.")
            sys.exit(0)
        else:
            self._execute_development()

    def _model_selection_phase(self) -> None:
        best_model_index = self._get_user_input().get("best_model", 0)
        print(f"[Orchestrator] User selected model index: {best_model_index}")

        if best_model_index == 0:
            iteration = self._status.get("iteration", 0) + 1
            if iteration >= self._max_outer_iterations:
                print(f"[Orchestrator] Max iterations ({self._max_outer_iterations}) reached. Stopping.")
                self._reset_status()
                return
            print(f"[Orchestrator] Validation rejected — retry {iteration}/{self._max_outer_iterations}")
            self._update_status({"phase": "Ready", "iteration": iteration})
            self._execute_development()
            return

        classifier_data = self._retrieve_classifier_data(best_model_index)
        if classifier_data is None:
            print("[Orchestrator] Selected model is invalid.")
            sys.exit(1)

        print(f"[Orchestrator] Selected: {classifier_data}")
        self._update_status({"phase": "Testing", "best_classifier_data": classifier_data})
        self._execute_development()

    def _testing_phase(self) -> None:
        print("[Orchestrator] Starting testing …")
        best_data  = self._status["best_classifier_data"]
        cl_id      = best_data["index"]
        model_path = os.path.join(CLASSIFIER_FOLDER, f"model_{cl_id}.sav")

        X_test, y_test = self._get_frames("test_set")

        test_orch = TestingOrchestrator(
            report_path=TESTING_REPORT_PATH,
            generalization_threshold=self._generalization_threshold,
        )
        report = test_orch.test_classifier(model_path, best_data, X_test, y_test)
        self._testing_report_view.display_training_report(report)

        self._update_status({"phase": "Results"})

        if not self._testing_mode:
            self._reset_user_input()
            print(f"Check testing report at {TESTING_REPORT_PATH}")
            print(f"Set approved=true/false in {USER_INPUT_PATH}.")
            sys.exit(0)
        else:
            self._execute_development()

    def _results_phase(self) -> None:
        approved = self._get_user_input().get("approved", False)

        if approved:
            best_data  = self._status["best_classifier_data"]
            model_path = os.path.join(CLASSIFIER_FOLDER, f"model_{best_data['index']}.sav")
            print(f"[Orchestrator] ✓ Approved. Final model at: {model_path}")
            print("[Orchestrator] Development completed successfully.")
        else:
            print("[Orchestrator] ✗ Rejected. Development failed.")

        self._reset_status()