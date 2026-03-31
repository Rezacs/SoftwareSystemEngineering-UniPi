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
from src.communicationController import CommunicationController

# ── Paths ──────────────────────────────────────────────────────────────
DATA_FOLDER            = "Data"
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


# ... (imports and helper functions remain the same)

class DevelopmentSystemOrchestrator:
    # ... (__init__ and status persistence remain the same)

    # ── state machine ──────────────────────────────────────────────────

    def run(self) -> None:
        print("=" * 60)
        print("DevelopmentSystemOrchestrator: run()")
        print(f"   Phase resumed : '{self._status['phase']}'")
        print(f"   Testing mode  : {self._testing_mode}")
        print("=" * 60)

        if self._testing_mode:
            self._start_time = time.time_ns()

        # BPMN: CALIBRATION SET RECEIVED
        if self._status["phase"] == "Starting":
            self._update_status({"phase": "Ready"})

        self._execute_development()

    # ── phases ─────────────────────────────────────────────────────────

    def _ready_phase(self) -> None:
        """BPMN Task: SET AVERAGE HYPERPARAMS"""
        val_orch = ValidationOrchestrator(
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
            self._stop(
                f"BPMN: Moving to 'DATA SCIENTIST: SET #ITERATIONS'. "
                f"Set 'max_iter' in {USER_INPUT_PATH}."
            )
        else:
            self._execute_development()

    def _learning_curve_phase(self) -> None:
        """
        BPMN Tasks: 
        1. DATA SCIENTIST: SET #ITERATIONS 
        2. CALIBRATE 
        3. GENERATE CALIBRATION REPORT 
        4. DATA SCIENTIST: CHECK CALIBRATION PLOT
        """
        user_input = self._get_user_input()
        good_iter  = user_input.get("good_max_iter", False)

        if not good_iter:
            # BPMN Gateway: #ITERATIONS FINE? -> NO
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
                self._stop(f"BPMN: Inspect Calibration Plot at {LEARNING_CURVE_PATH}.")
            else:
                self._execute_development()
        else:
            # BPMN Gateway: #ITERATIONS FINE? -> YES
            print(f"[Orchestrator] Iterations approved: {self._status['max_iter']}")
            self._update_status({"phase": "Validation"})
            self._execute_development()

    def _grid_search_phase(self) -> None:
        """BPMN Tasks: SET HYPERPARAMS & GENERATE VALIDATION REPORT"""
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
            self._stop(f"BPMN Task: DATA SCIENTIST: CHECK VALIDATION RESULTS")
        else:
            self._execute_development()

    def _model_selection_phase(self) -> None:
        """BPMN Gateway: IS THERE A VALID CLASSIFIER?"""
        best_model_index = self._get_user_input().get("best_model", 0)
        print(f"[Orchestrator] User selected model index: {best_model_index}")

        if best_model_index == 0:
            # BPMN Gateway Choice: NO (Looping back)
            iteration = self._status.get("iteration", 0) + 1
            if iteration >= self._max_outer_iterations:
                # BPMN: Max Iterations reached (Process Ends/Sends Config)
                print(f"[Orchestrator] Max outer iterations reached.")
                self._reset_status()
                return
            
            # BPMN Loop: Back to SET HYPERPARAMS
            self._update_status({"phase": "Ready", "iteration": iteration})
            self._execute_development()
            return

        # BPMN Gateway Choice: YES
        classifier_data = self._retrieve_classifier_data(best_model_index)
        if classifier_data is None:
            self._stop(f"Invalid selection. Please choose a valid classifier.")

        print(f"[Orchestrator] Selected classifier: {classifier_data}")
        self._update_status({"phase": "Testing", "best_classifier_data": classifier_data})
        self._execute_development()

    def _testing_phase(self) -> None:
        """BPMN Tasks: GENERATE TEST REPORT & DATA SCIENTIST: CHECK TEST RESULTS"""
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
            self._stop(f"BPMN Gateway: TEST PASSED?")
        else:
            self._execute_development()

    def _results_phase(self) -> None:
        """BPMN Events: CLASSIFIER SENT or CONFIGURATION SENT"""
        approved = self._get_user_input().get("approved", False)

        best_data  = self._status["best_classifier_data"]
        cl_id      = best_data["index"]
        model_path = os.path.join(CLASSIFIER_FOLDER, f"model_{cl_id}.sav")

        if approved:
            # BPMN Gateway: YES -> CLASSIFIER SENT
            print(f"[Orchestrator] ✓ Approved — sending classifier...")
            self._comm.send_classifier(model_path)
        else:
            # BPMN Gateway: NO -> CONFIGURATION SENT
            print(f"[Orchestrator] ✗ Rejected — sending report...")
            self._comm.send_testing_report(TESTING_REPORT_PATH)

        self._reset_status()