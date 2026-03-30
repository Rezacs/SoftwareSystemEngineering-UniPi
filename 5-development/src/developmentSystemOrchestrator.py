import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

import pandas as pd

from Data.learningPlot import LearningPlot
from Data.validationReport import ValidationReport
from Data.testingReport import TestingReport
from Data.hyperParameters import HyperParameters
from Data.learningSet import LearningSet
from Data.preparedSession import PreparedSession
from src.trainingOrchestrator import TrainingOrchestrator
from src.validationOrchestrator import ValidationOrchestrator
from src.testingOrchestrator import TestingOrchestrator
from src.learningPlotView import LearningPlotView
from src.validationReportView import ValidationReportView
from src.testingReportView import TestingReportView

# ── Paths ──────────────────────────────────────────────────────────────
DATA_FOLDER            = "data"
STATUS_FILE_PATH       = os.path.join(DATA_FOLDER, "internal/status.json")
CLASSIFIER_FOLDER      = os.path.join(DATA_FOLDER, "classifiers/")
LEARNING_CURVE_PATH    = os.path.join(DATA_FOLDER, "reports/learning_curve.png")
VALIDATION_REPORT_PATH = os.path.join(DATA_FOLDER, "reports/validation_report.json")
TESTING_REPORT_PATH    = os.path.join(DATA_FOLDER, "reports/testing_report.json")
USER_INPUT_PATH        = os.path.join(DATA_FOLDER, "configs/user_input.json")


FEATURE_COLS = ["skillOverall", "socialInfluence", "injuriesImpact"]


def _sessions_to_frames(sessions):
    X = pd.DataFrame(
        [{col: getattr(s, col) for col in FEATURE_COLS} for s in sessions]
    )
    y = [s.label for s in sessions]
    return X, y


class DevelopmentSystemOrchestrator:
    """
    State-machine orchestrator for the full development cycle.

    Stop&Go pattern (testing_mode=False):
        Each phase ends with sys.exit(0). The user inspects outputs,
        edits data/configs/user_input.json, then re-runs main.py.
        The status is persisted in data/internal/status.json so each
        restart resumes exactly where it left off.

    Testing mode (testing_mode=True):
        User decisions are simulated on-the-fly; the app never stops
        between phases. Timestamps are recorded for benchmarking.

    Phases:
        Starting → Ready → LearningCurve → Validation
        → ValidationReport → Testing → Results
    """

    def __init__(
        self,
        learning_set: LearningSet,
        hyper_param_configs: List[HyperParameters],
        overfitting_threshold: float = 0.1,
        generalization_threshold: float = 0.15,
        max_outer_iterations: int = 3,
        testing_mode: bool = False,
    ) -> None:
        self._learning_set             = learning_set
        self._hyper_param_configs      = hyper_param_configs
        self._overfitting_threshold    = overfitting_threshold
        self._generalization_threshold = generalization_threshold
        self._max_outer_iterations     = max_outer_iterations
        self._testing_mode             = testing_mode

        # Timestamps (testing mode only)
        self._start_time: Optional[int] = None

        # Load persisted state — never overwrite it here
        self._status: Dict[str, Any] = self._load_status()

        # Views
        self._learning_plot_view     = LearningPlotView()
        self._validation_report_view = ValidationReportView()
        self._testing_report_view    = TestingReportView()

    # ── status persistence ─────────────────────────────────────────────
    def _default_status(self) -> Dict[str, Any]:
        return {
            "phase":                "Starting",   # ← "Starting", not "Ready"
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
        """Full reset back to Starting so the next run() begins fresh."""
        self._status = self._default_status()
        self._save_status()

    # ── user input ─────────────────────────────────────────────────────
    def _write_user_input_template(self) -> None:
        """
        Write a template user_input.json for the current phase.
        Called once per stop, so the user knows exactly what to fill in.
        Previous values are preserved where possible so the user only
        needs to change what matters.
        """
        phase = self._status["phase"]

        # Start from whatever is already on disk so prior fields survive
        existing: dict = {}
        if os.path.isfile(USER_INPUT_PATH):
            try:
                with open(USER_INPUT_PATH, "r", encoding="UTF-8") as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, OSError):
                existing = {}

        if phase == "LearningCurve":
            payload = {
                "max_iter":      existing.get("max_iter", self._status.get("max_iter", 200)),
                "good_max_iter": False,   # user must explicitly set this to True
            }
        elif phase == "ValidationReport":
            payload = {
                "best_model": existing.get("best_model", 0),
            }
        elif phase == "Results":
            payload = {
                "approved": False,        # user must explicitly set this to True
            }
        else:
            payload = existing  # nothing to change for other phases

        os.makedirs(os.path.dirname(USER_INPUT_PATH), exist_ok=True)
        with open(USER_INPUT_PATH, "w", encoding="UTF-8") as f:
            json.dump(payload, f, indent="\t")

    def _get_user_input(self) -> dict:
        """Return user input — simulated in testing mode, read from disk otherwise."""
        if self._testing_mode:
            return self._simulate_user_input()
        try:
            with open(USER_INPUT_PATH, "r", encoding="UTF-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[Orchestrator] ERROR: {USER_INPUT_PATH} not found.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"[Orchestrator] ERROR: {USER_INPUT_PATH} contains invalid JSON.")
            sys.exit(1)

    def _simulate_user_input(self) -> dict:
        """Generate a plausible user decision automatically (testing mode only)."""
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

    # ── stop helper ────────────────────────────────────────────────────
    def _stop(self, message: str) -> None:
        """
        Write the user-input template, print instructions, and exit.
        Only called in interactive (stop&go) mode.
        """
        self._write_user_input_template()
        print(f"\n[Orchestrator] STOP — {message}")
        print(f"  → Edit {USER_INPUT_PATH}")
        print(f"  → Then re-run main.py to continue.\n")
        sys.exit(0)

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
        print(f"  Phase resumed: '{self._status['phase']}'")
        print(f"  Testing mode : {self._testing_mode}")
        print("=" * 60)

        if self._testing_mode:
            self._start_time = time.time_ns()

        # ── Only initialise on a brand-new run ────────────────────────
        # In stop&go mode the status file already holds the correct phase
        # from the previous run — we must NOT overwrite it.
        if self._status["phase"] == "Starting":
            self._update_status({"phase": "Ready"})

        self._execute_development()

    def _execute_development(self) -> None:
        dispatch = {
            "Ready":            self._ready_phase,
            "LearningCurve":    self._learning_curve_phase,
            "Validation":       self._grid_search_phase,
            "ValidationReport": self._model_selection_phase,
            "Testing":          self._testing_phase,
            "Results":          self._results_phase,
        }
        phase   = self._status["phase"]
        handler = dispatch.get(phase)
        if handler:
            handler()
        else:
            print(f"[Orchestrator] Unknown phase: '{phase}' — resetting.")
            self._reset_status()

    # ── phases ─────────────────────────────────────────────────────────
    def _ready_phase(self) -> None:
        """Compute average hyper-parameters; advance to LearningCurve."""
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
            # The template written here tells the user what max_iter to set
            self._stop(
                f"Set 'max_iter' (int) and leave 'good_max_iter': false "
                f"in {USER_INPUT_PATH}, then re-run."
            )
        else:
            self._execute_development()

    def _learning_curve_phase(self) -> None:
        """Generate learning curve; loop until user approves iteration count."""
        user_input = self._get_user_input()
        good_iter  = user_input.get("good_max_iter", False)

        if not good_iter:
            # Accept whatever max_iter the user wrote (or keep the old one)
            max_iter = user_input.get("max_iter", self._status["max_iter"])
            self._update_status({"max_iter": max_iter})
            print(f"[Orchestrator] Generating learning curve ({max_iter} epochs) …")

            X_train, y_train = self._get_frames("training_set")
            to = TrainingOrchestrator()
            params = dict(self._status.get("avg_params", {}))
            params["max_iter"] = max_iter
            to.set_parameters(params)

            plot = to.generate_learning_curve(X_train, y_train, LEARNING_CURVE_PATH)
            self._learning_plot_view.display_learning_plot(plot)

            if not self._testing_mode:
                self._stop(
                    f"Inspect the curve at {LEARNING_CURVE_PATH}. "
                    f"Adjust 'max_iter' if needed, then set 'good_max_iter': true "
                    f"to proceed."
                )
            else:
                self._execute_development()

        else:
            print(f"[Orchestrator] Iterations approved: {self._status['max_iter']}")
            self._update_status({"phase": "Validation"})
            self._execute_development()

    def _grid_search_phase(self) -> None:
        """Train one classifier per HP config; write validation report."""
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
            self._stop(
                f"Inspect {VALIDATION_REPORT_PATH}. "
                f"Set 'best_model' to the chosen index (0 = reject all)."
            )
        else:
            self._execute_development()

    def _model_selection_phase(self) -> None:
        """Read user's model choice; go to Testing or retry from Ready."""
        best_model_index = self._get_user_input().get("best_model", 0)
        print(f"[Orchestrator] User selected model index: {best_model_index}")

        if best_model_index == 0:
            iteration = self._status.get("iteration", 0) + 1
            if iteration >= self._max_outer_iterations:
                print(
                    f"[Orchestrator] Max outer iterations "
                    f"({self._max_outer_iterations}) reached — stopping."
                )
                self._reset_status()
                return
            print(
                f"[Orchestrator] Validation rejected — "
                f"retry {iteration}/{self._max_outer_iterations}"
            )
            self._update_status({"phase": "Ready", "iteration": iteration})
            self._execute_development()
            return

        classifier_data = self._retrieve_classifier_data(best_model_index)
        if classifier_data is None:
            print(f"[Orchestrator] Model index {best_model_index} is not valid.")
            if not self._testing_mode:
                self._stop(
                    f"Choose a valid model index from {VALIDATION_REPORT_PATH}."
                )
            else:
                sys.exit(1)

        print(f"[Orchestrator] Selected classifier: {classifier_data}")
        self._update_status({"phase": "Testing", "best_classifier_data": classifier_data})
        self._execute_development()

    def _testing_phase(self) -> None:
        """Run final acceptance test on the selected classifier."""
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
            self._stop(
                f"Inspect {TESTING_REPORT_PATH}. "
                f"Set 'approved': true to accept the classifier, false to reject."
            )
        else:
            self._execute_development()

    def _results_phase(self) -> None:
        """Final decision: publish classifier or declare failure."""
        approved = self._get_user_input().get("approved", False)

        if self._testing_mode and self._start_time is not None:
            elapsed_ns = time.time_ns() - self._start_time
            print(f"[Orchestrator] ⏱  Total cycle time: {elapsed_ns / 1e9:.3f} s")

        if approved:
            best_data  = self._status["best_classifier_data"]
            model_path = os.path.join(CLASSIFIER_FOLDER, f"model_{best_data['index']}.sav")
            print(f"[Orchestrator] ✓ Approved. Final model at: {model_path}")
            print("[Orchestrator] Development completed successfully.")
        else:
            print("[Orchestrator] ✗ Rejected. Development failed.")

        # Always reset so the next run() starts fresh
        self._reset_status()