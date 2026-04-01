import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

import pandas as pd

from Data.hyperParameters import HyperParameters
from Data.learningSet import LearningSet
from src.trainingOrchestrator import TrainingOrchestrator
from src.validationOrchestrator import ValidationOrchestrator
from src.testingOrchestrator import TestingOrchestrator
from src.learningPlotView import LearningPlotView
from src.validationReportView import ValidationReportView
from src.testingReportView import TestingReportView
from src.communicationController import CommunicationController
from src.config import (
    STATUS_FILE_PATH,
    CLASSIFIER_FOLDER,
    LEARNING_CURVE_PATH,
    VALIDATION_REPORT_PATH,
    TESTING_REPORT_PATH,
    USER_INPUT_PATH,
    FEATURE_COLS,
    OVERFITTING_THRESHOLD,
    GENERALIZATION_THRESHOLD,
    MAX_OUTER_ITERATIONS,
    DEFAULT_MAX_ITER,
)


def _sessions_to_frames(sessions):
    X = pd.DataFrame(
        [{col: getattr(s, col) for col in FEATURE_COLS} for s in sessions]
    )
    y = [s.label for s in sessions]
    return X, y


class DevelopmentSystemOrchestrator:
    """
    State-machine orchestrator for the Development System.
    Every public method name matches its BPMN task label exactly.

    Phase → BPMN method mapping:
        "Ready"            → set_average_hyperparams()
        "LearningCurve"    → set_iterations()
        "Validation"       → generate_validation_report()
        "ValidationReport" → is_there_a_valid_classifier()
        "Testing"          → generate_test_report()
        "Results"          → test_passed()

    All thresholds and paths are loaded from Data/configs/config.json.
    """

    def __init__(
        self,
        learning_set: LearningSet,
        hyper_param_configs: List[HyperParameters],
        overfitting_threshold: float = OVERFITTING_THRESHOLD,
        generalization_threshold: float = GENERALIZATION_THRESHOLD,
        max_outer_iterations: int = MAX_OUTER_ITERATIONS,
        testing_mode: bool = False,
    ) -> None:
        self._learning_set             = learning_set
        self._hyper_param_configs      = hyper_param_configs
        self._overfitting_threshold    = overfitting_threshold
        self._generalization_threshold = generalization_threshold
        self._max_outer_iterations     = max_outer_iterations
        self._testing_mode             = testing_mode

        self._start_time: Optional[int] = None
        self._status: Dict[str, Any]    = self._load_status()

        self._learning_plot_view     = LearningPlotView()
        self._validation_report_view = ValidationReportView()
        self._testing_report_view    = TestingReportView()
        self._comm                   = CommunicationController()

    # ── status persistence ─────────────────────────────────────────────

    def _default_status(self) -> Dict[str, Any]:
        return {
            "phase":                "Starting",
            "max_iter":             DEFAULT_MAX_ITER,
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

    def _write_user_input_template(self) -> None:
        phase    = self._status["phase"]
        existing: dict = {}
        if os.path.isfile(USER_INPUT_PATH):
            try:
                with open(USER_INPUT_PATH, "r", encoding="UTF-8") as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, OSError):
                existing = {}

        if phase == "LearningCurve":
            payload = {
                "max_iter":      existing.get("max_iter", self._status.get("max_iter", DEFAULT_MAX_ITER)),
                "good_max_iter": False,
            }
        elif phase == "ValidationReport":
            payload = {"best_model": existing.get("best_model", 0)}
        elif phase == "Results":
            payload = {"approved": False}
        else:
            payload = existing

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
            print(f"[Orchestrator] ERROR: {USER_INPUT_PATH} not found.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"[Orchestrator] ERROR: {USER_INPUT_PATH} contains invalid JSON.")
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

    # ── stop&go helper ─────────────────────────────────────────────────

    def _stop(self, message: str) -> None:
        self._write_user_input_template()
        print(f"\n[Orchestrator] STOP — {message}")
        print(f"  → Edit {USER_INPUT_PATH}")
        print(f"  → Then re-run main.py to continue.\n")
        sys.exit(0)

    # ── internal helpers ───────────────────────────────────────────────

    def _get_frames(self, split: str):
        return _sessions_to_frames(getattr(self._learning_set, split))

    def _retrieve_classifier_data(self, model_index: int) -> Optional[dict]:
        with open(VALIDATION_REPORT_PATH, "r", encoding="UTF-8") as f:
            report = json.load(f)
        entry = next(
            (item for item in report["best_classifiers"] if item["index"] == model_index), None
        )
        return entry if (entry and entry["valid"]) else None

    # ── state machine entry point ──────────────────────────────────────

    def run(self) -> None:
        """BPMN start event: CALIBRATION SET RECEIVED."""
        print("=" * 60)
        print("DevelopmentSystemOrchestrator: run()")
        print(f"  Phase resumed : '{self._status['phase']}'")
        print(f"  Testing mode  : {self._testing_mode}")
        print("=" * 60)

        if self._testing_mode:
            self._start_time = time.time_ns()

        if self._status["phase"] == "Starting":
            self._update_status({"phase": "Ready"})

        self._execute_development()

    def _execute_development(self) -> None:
        """Routes the current phase to its BPMN-named handler."""
        dispatch = {
            "Ready":            self.set_average_hyperparams,
            "LearningCurve":    self.set_iterations,
            "Validation":       self.generate_validation_report,
            "ValidationReport": self.is_there_a_valid_classifier,
            "Testing":          self.generate_test_report,
            "Results":          self.test_passed,
        }
        phase   = self._status["phase"]
        handler = dispatch.get(phase)
        if handler:
            handler()
        else:
            print(f"[Orchestrator] Unknown phase: '{phase}' — resetting.")
            self._reset_status()

    # ── BPMN tasks ─────────────────────────────────────────────────────

    def set_average_hyperparams(self) -> None:
        """
        BPMN Task: SET AVERAGE HYPERPARAMS
        Computes mean num_layers / num_neurons across all HP configs
        and persists them as the baseline for calibration.
        """
        val_orch   = ValidationOrchestrator(
            hp_configs=self._hyper_param_configs,
            classifier_folder=CLASSIFIER_FOLDER,
            report_path=VALIDATION_REPORT_PATH,
            training_orchestrator=TrainingOrchestrator(),
            overfitting_threshold=self._overfitting_threshold,
        )
        avg_params = val_orch.retrieve_average_parameters()
        print(f"[Orchestrator] SET AVERAGE HYPERPARAMS: {avg_params}")
        self._update_status({"avg_params": avg_params, "phase": "LearningCurve"})

        if not self._testing_mode:
            self._stop(
                f"BPMN: DATA SCIENTIST: SET #ITERATIONS — "
                f"set 'max_iter' in {USER_INPUT_PATH}."
            )
        else:
            self._execute_development()

    def set_iterations(self) -> None:
        """
        BPMN Tasks:
          • DATA SCIENTIST: SET #ITERATIONS       (user edits max_iter)
          • CALIBRATE                             (fits MLP for N epochs)
          • GENERATE CALIBRATION REPORT           (saves loss_curve_ PNG)
          • DATA SCIENTIST: CHECK CALIBRATION PLOT (user approves)

        BPMN Gateway: #ITERATIONS FINE?
          NO  → regenerates calibration report with updated max_iter
          YES → advances to generate_validation_report()
        """
        user_input = self._get_user_input()
        good_iter  = user_input.get("good_max_iter", False)

        if not good_iter:
            max_iter = user_input.get("max_iter", self._status["max_iter"])
            self._update_status({"max_iter": max_iter})
            print(f"[Orchestrator] CALIBRATE — {max_iter} epochs …")

            X_train, y_train = self._get_frames("training_set")
            to = TrainingOrchestrator()
            params = dict(self._status.get("avg_params", {}))
            params["max_iter"] = max_iter
            to.set_parameters(params)

            plot = to.generate_calibration_report(X_train, y_train, LEARNING_CURVE_PATH)
            self._learning_plot_view.display_learning_plot(plot)

            if not self._testing_mode:
                self._stop(
                    f"BPMN: DATA SCIENTIST: CHECK CALIBRATION PLOT — "
                    f"inspect {LEARNING_CURVE_PATH}. "
                    f"Adjust 'max_iter' if needed, then set 'good_max_iter': true."
                )
            else:
                self._execute_development()
        else:
            print(f"[Orchestrator] #ITERATIONS FINE — {self._status['max_iter']} approved.")
            self._update_status({"phase": "Validation"})
            self._execute_development()

    def generate_validation_report(self) -> None:
        """
        BPMN Tasks:
          • SET HYPERPARAMS             (one config per grid-search entry)
          • GENERATE VALIDATION REPORT  (trains all configs, writes JSON)

        Followed by BPMN stop:
          • DATA SCIENTIST: CHECK VALIDATION RESULTS
        """
        print("[Orchestrator] SET HYPERPARAMS & GENERATE VALIDATION REPORT …")
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
        report = val_orch.generate_validation_report(X_train, y_train, X_val, y_val)
        self._validation_report_view.display_validation_report(report)
        self._update_status({"phase": "ValidationReport"})

        if not self._testing_mode:
            self._stop(
                f"BPMN: DATA SCIENTIST: CHECK VALIDATION RESULTS — "
                f"inspect {VALIDATION_REPORT_PATH}. "
                f"Set 'best_model' to chosen index (0 = reject all)."
            )
        else:
            self._execute_development()

    def is_there_a_valid_classifier(self) -> None:
        """
        BPMN Gateway: IS THERE A VALID CLASSIFIER?
          NO  → loop back to set_average_hyperparams() (up to max_outer_iterations)
          YES → advance to generate_test_report()
        """
        best_model_index = self._get_user_input().get("best_model", 0)
        print(f"[Orchestrator] IS THERE A VALID CLASSIFIER? → index={best_model_index}")

        if best_model_index == 0:
            iteration = self._status.get("iteration", 0) + 1
            if iteration >= self._max_outer_iterations:
                print(
                    f"[Orchestrator] Max outer iterations "
                    f"({self._max_outer_iterations}) reached — CONFIGURATION SENT."
                )
                self._comm.send_testing_report(TESTING_REPORT_PATH)
                self._reset_status()
                return
            print(
                f"[Orchestrator] No valid classifier — "
                f"retry {iteration}/{self._max_outer_iterations}. "
                f"Looping back to SET AVERAGE HYPERPARAMS."
            )
            self._update_status({"phase": "Ready", "iteration": iteration})
            self._execute_development()
            return

        classifier_data = self._retrieve_classifier_data(best_model_index)
        if classifier_data is None:
            print(f"[Orchestrator] Model index {best_model_index} is not valid.")
            if not self._testing_mode:
                self._stop(f"Choose a valid index from {VALIDATION_REPORT_PATH}.")
            else:
                sys.exit(1)

        print(f"[Orchestrator] Valid classifier found: {classifier_data}")
        self._update_status({"phase": "Testing", "best_classifier_data": classifier_data})
        self._execute_development()

    def generate_test_report(self) -> None:
        """
        BPMN Tasks:
          • GENERATE TEST REPORT                (runs model on test set, writes JSON)
          • DATA SCIENTIST: CHECK TEST RESULTS  (user inspects, sets approved flag)
        """
        print("[Orchestrator] GENERATE TEST REPORT …")
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
                f"BPMN: DATA SCIENTIST: CHECK TEST RESULTS — "
                f"inspect {TESTING_REPORT_PATH}. "
                f"Set 'approved': true to accept, false to reject."
            )
        else:
            self._execute_development()

    def test_passed(self) -> None:
        """
        BPMN Gateway: TEST PASSED?
          YES → CLASSIFIER SENT  (to Classification System)
          NO  → CONFIGURATION SENT  (testing report to Messaging System)
        """
        approved   = self._get_user_input().get("approved", False)
        best_data  = self._status["best_classifier_data"]
        cl_id      = best_data["index"]
        model_path = os.path.join(CLASSIFIER_FOLDER, f"model_{cl_id}.sav")

        if self._testing_mode and self._start_time is not None:
            elapsed_ns = time.time_ns() - self._start_time
            print(f"[Orchestrator] ⏱  Total cycle time: {elapsed_ns / 1e9:.3f} s")

        if approved:
            print("[Orchestrator] TEST PASSED — CLASSIFIER SENT to Classification System.")
            self._comm.send_classifier(model_path)
        else:
            print("[Orchestrator] TEST NOT PASSED — CONFIGURATION SENT to Messaging System.")
            self._comm.send_testing_report(TESTING_REPORT_PATH)

        self._reset_status()