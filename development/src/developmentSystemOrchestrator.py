
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
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

# ── Config/log paths resolved from repository root (cross-platform) ─────────
REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = str(REPO_ROOT / "config" / "developmentConfig.json")
LOG_PATH = str(REPO_ROOT / "logs" / "developmentLog.json")
print(f"[Orchestrator] Loading configuration from: {CONFIG_PATH}")


def _load_config() -> dict:
    if not os.path.isfile(CONFIG_PATH):
        raise FileNotFoundError(
            f"Configuration file not found: {CONFIG_PATH}\n"
            f"Make sure ../config/developmentConfig.json exists before running."
        )
    with open(CONFIG_PATH, "r", encoding="UTF-8") as f:
        return json.load(f)


def _sessions_to_frames(sessions, feature_cols: List[str]):
    X = pd.DataFrame(
        [{col: getattr(s, col) for col in feature_cols} for s in sessions]
    )
    y = [s.label for s in sessions]
    return X, y


class DevelopmentSystemOrchestrator:

    def __init__(
        self,
        learning_set: LearningSet,
        testing_mode: bool = False,
    ) -> None:
        # ── load config ────────────────────────────────────────────────
        cfg = _load_config()
        
        net  = cfg["network"]
        pth  = cfg["paths"]
        mdl  = cfg["model"]
        pipe = cfg["pipeline"]

        # paths
        self._status_file_path       = pth["status_file"]
        self._classifier_folder      = pth["classifier_folder"]
        self._learning_curve_path    = pth["learning_curve"]
        self._validation_report_path = pth["validation_report"]
        self._testing_report_path    = pth["testing_report"]
        self._user_input_path        = pth["user_input"]

        # model
        self._feature_cols = mdl["feature_cols"]
        self._score_min    = int(mdl["score_min"])
        self._score_max    = int(mdl["score_max"])

        # pipeline thresholds
        self._overfitting_threshold    = float(pipe["overfitting_threshold"])
        self._generalization_threshold = float(pipe["generalization_threshold"])
        self._max_outer_iterations     = int(pipe["max_outer_iterations"])
        self._default_max_iter         = int(pipe["default_max_iter"])

        # domain objects
        self._learning_set        = learning_set
        self._hyper_param_configs = self._build_hyper_param_configs(cfg)
        self._testing_mode        = testing_mode
        self._start_time: Optional[int] = None

        # persisted state
        self._status: Dict[str, Any] = self._load_status()

        # views
        self._learning_plot_view     = LearningPlotView()
        self._validation_report_view = ValidationReportView()
        self._testing_report_view    = TestingReportView()

        # communication (all network params from config)
        self._comm = CommunicationController(
            listen_host         = net["listen_host"],
            listen_port         = int(net["listen_port"]),
            segregation_ip      = net["segregation_system"]["ip"],
            segregation_port    = int(net["segregation_system"]["port"]),
            production_ip       = net["production_system"]["ip"],
            production_port     = int(net["production_system"]["port"]),
            production_endpoint = net["production_system"]["endpoint"],
            received_data_path  = pth["received_data"],
            rejected_report_path= pth["rejected_report"],
        )
        
        # log 
        self._log_path = LOG_PATH
        self._session_key = "current_session"

    # ── status persistence ─────────────────────────────────────────────

    def _default_status(self) -> Dict[str, Any]:
        return {
            "phase":                "Starting",
            "max_iter":             self._default_max_iter,
            "avg_params":           {},
            "best_classifier_data": None,
            "iteration":            0,
        }

    def _load_status(self) -> Dict[str, Any]:
        if os.path.isfile(self._status_file_path):
            with open(self._status_file_path, "r", encoding="UTF-8") as f:
                return json.load(f)
        return self._default_status()

    def _save_status(self) -> None:
        os.makedirs(os.path.dirname(self._status_file_path), exist_ok=True)
        with open(self._status_file_path, "w", encoding="UTF-8") as f:
            json.dump(self._status, f, indent="\t")

    def _update_status(self, updates: Dict[str, Any]) -> None:
        self._status.update(updates)
        self._save_status()

    def _reset_status(self) -> None:
        self._status = self._default_status()
        self._save_status()

    # ── user input ─────────────────────────────────────────────────────

    def _write_user_input_template(self) -> None:
        """Write a phase-specific template to user_input.json."""
        phase    = self._status["phase"]
        existing: dict = {}
        if os.path.isfile(self._user_input_path):
            try:
                with open(self._user_input_path, "r", encoding="UTF-8") as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, OSError):
                existing = {}

        if phase == "LearningCurve":
            payload = {
                "max_iter":      existing.get("max_iter", self._status.get("max_iter", self._default_max_iter)),
                "good_max_iter": False,
            }
        elif phase == "ValidationReport":
            payload = {"best_model": existing.get("best_model", 0)}
        elif phase == "Results":
            payload = {"approved": False}
        else:
            payload = existing

        os.makedirs(os.path.dirname(self._user_input_path), exist_ok=True)
        with open(self._user_input_path, "w", encoding="UTF-8") as f:
            json.dump(payload, f, indent="\t")

    def _get_user_input(self) -> dict:
        """
        testing_mode=False → reads user_input.json (human decision)
        testing_mode=True  → simulates decision from report files
        """
        if self._testing_mode:
            return self._simulate_user_input()
        try:
            with open(self._user_input_path, "r", encoding="UTF-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[Orchestrator] ERROR: {self._user_input_path} not found.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"[Orchestrator] ERROR: {self._user_input_path} contains invalid JSON.")
            sys.exit(1)

    def _simulate_user_input(self) -> dict:
        """Auto-generate a plausible human decision (testing mode only)."""
        phase = self._status["phase"]
        if phase == "LearningCurve":
            return {"max_iter": 300, "good_max_iter": True}
        elif phase == "ValidationReport":
            with open(self._validation_report_path, "r", encoding="UTF-8") as f:
                report = json.load(f)
            index = next(
                (item["index"] for item in report["best_classifiers"] if item["valid"]), 0
            )
            return {"best_model": index}
        elif phase == "Results":
            with open(self._testing_report_path, "r", encoding="UTF-8") as f:
                report = json.load(f)
            return {"approved": report["errors"]["passed"]}
        return {}

    # ── stop&go helper ─────────────────────────────────────────────────

    def _stop(self, message: str) -> None:
        # stop helper to handle different stopping points in the BPMN
        self._write_user_input_template()
        print(f"\n[Orchestrator] {message}")
        print(f"  → 1. Edit: {self._user_input_path}")
        
        if not self._testing_mode:
            
            while True:
                choice = input(f"  → Have you saved your decisions in the JSON? (y/n): ").strip().lower()
                if choice == 'y':
                   
                    self._execute_development()
                    break
                else:
                    print("  [Waiting...] Please update the file before continuing.")
        else:
           
            self._execute_development()

    # ── internal helpers ───────────────────────────────────────────────

    def _get_frames(self, split: str):
        return _sessions_to_frames(
            getattr(self._learning_set, split), self._feature_cols
        )

    def _retrieve_classifier_data(self, model_index: int) -> Optional[dict]:
        with open(self._validation_report_path, "r", encoding="UTF-8") as f:
            report = json.load(f)
        entry = next(
            (item for item in report["best_classifiers"] if item["index"] == model_index), None
        )
        return entry if (entry and entry["valid"]) else None

    def _make_training_orchestrator(self) -> TrainingOrchestrator:
        return TrainingOrchestrator(
            feature_cols=self._feature_cols,
            score_min=self._score_min,
            score_max=self._score_max,
        )
    
    def _build_hyper_param_configs(self, cfg: dict) -> List[HyperParameters]:
        """
    Construct HyperParameters internally from config.
        """
        hp_list = cfg.get("hyperparameters", [])
        return [
        HyperParameters(
            classifier_id  = hp["classifier_id"],
            num_layers     = int(hp["num_layers"]),
            num_neurons    = int(hp["num_neurons"]),
            num_iterations = int(hp["num_iterations"]),
        )
        for hp in hp_list
    ]

    # ── Logging Logic ──────────────────────────────────────────────────

    def _init_log(self) -> None:
        """Initialize the log file if it doesn't exist and prepare the session."""
        os.makedirs(os.path.dirname(self._log_path), exist_ok=True)
        
        data = {}
        if os.path.isfile(self._log_path):
            with open(self._log_path, "r", encoding="UTF-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}

        if self._session_key not in data:
            data[self._session_key] = []
            
        with open(self._log_path, "w", encoding="UTF-8") as f:
            json.dump(data, f, indent="\t")

    def _log_event(self, process: str, decision: str) -> None:
        """Appends a human-decision event to the log."""
        if not os.path.isfile(self._log_path):
            self._init_log()

        with open(self._log_path, "r+", encoding="UTF-8") as f:
            data = json.load(f)
            event = {
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "process": process,
                "decision": decision
            }
            data[self._session_key].append(event)
            f.seek(0)
            json.dump(data, f, indent="\t")
            f.truncate()

    def _finalize_log(self, output_type: str) -> None:
        """Finalizes the session by adding output and renaming the key to current timestamp."""
        if not os.path.isfile(self._log_path): return

        with open(self._log_path, "r+", encoding="UTF-8") as f:
            data = json.load(f)
            if self._session_key in data:
                session_data = data.pop(self._session_key)
                # Add final output entry
                session_data.append({"output": output_type})
                
                # Create final key with current ISO timestamp
                final_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                data[final_timestamp] = session_data
                
                f.seek(0)
                json.dump(data, f, indent="\t")
                f.truncate()
                
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
            self._init_log()
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
        """BPMN Task: SET AVERAGE HYPERPARAMS"""
        val_orch   = ValidationOrchestrator(
            hp_configs=self._hyper_param_configs,
            classifier_folder=self._classifier_folder,
            report_path=self._validation_report_path,
            training_orchestrator=self._make_training_orchestrator(),
            overfitting_threshold=self._overfitting_threshold,
        )
        avg_params = val_orch.retrieve_average_parameters()
        print(f"[Orchestrator] SET AVERAGE HYPERPARAMS: {avg_params}")
        self._update_status({"avg_params": avg_params, "phase": "LearningCurve"})

        if not self._testing_mode:
            self._stop(
                f"BPMN: DATA SCIENTIST: SET #ITERATIONS — "
                f"set 'max_iter' in {self._user_input_path}."
            )
        else:
            self._execute_development()

    def set_iterations(self) -> None:
        """
        BPMN Tasks:
          • DATA SCIENTIST: SET #ITERATIONS
          • CALIBRATE
          • GENERATE CALIBRATION REPORT
          • DATA SCIENTIST: CHECK CALIBRATION PLOT

        BPMN Gateway: #ITERATIONS FINE?
          NO  → regenerate calibration report with updated max_iter
          YES → advance to generate_validation_report()
        """
        user_input = self._get_user_input()
        good_iter  = user_input.get("good_max_iter", False)

        if not good_iter:
            max_iter = user_input.get("max_iter", self._status["max_iter"])
            self._update_status({"max_iter": max_iter})
            self._log_event("learning curve", f"set #iterations to {max_iter}")
            print(f"[Orchestrator] CALIBRATE — {max_iter} epochs …")

            X_train, y_train = self._get_frames("training_set")
            to = self._make_training_orchestrator()
            params = dict(self._status.get("avg_params", {}))
            params["max_iter"] = max_iter
            to.set_parameters(params)

            plot = to.generate_calibration_report(X_train, y_train, self._learning_curve_path)
            self._learning_plot_view.display_learning_plot(plot)

            if not self._testing_mode:
                self._stop(
                    f"BPMN: DATA SCIENTIST: CHECK CALIBRATION PLOT — "
                    f"inspect {self._learning_curve_path}. "
                    f"Adjust 'max_iter' if needed, then set 'good_max_iter': true."
                )
            else:
                self._execute_development()
        else:
            self._log_event("set #iterations", f"approved iterations: {self._status['max_iter']}")
            print(f"[Orchestrator] #ITERATIONS FINE — {self._status['max_iter']} approved.")
            self._update_status({"phase": "Validation"})
            self._execute_development()

    def generate_validation_report(self) -> None:
        """
        BPMN Tasks:
          • SET HYPERPARAMS
          • GENERATE VALIDATION REPORT
          • DATA SCIENTIST: CHECK VALIDATION RESULTS
        """
        print("[Orchestrator] SET HYPERPARAMS & GENERATE VALIDATION REPORT …")
        X_train, y_train = self._get_frames("training_set")
        X_val,   y_val   = self._get_frames("validation_set")

        to = self._make_training_orchestrator()
        to.set_parameters({"max_iter": self._status["max_iter"]})

        val_orch = ValidationOrchestrator(
            hp_configs=self._hyper_param_configs,
            classifier_folder=self._classifier_folder,
            report_path=self._validation_report_path,
            training_orchestrator=to,
            overfitting_threshold=self._overfitting_threshold,
        )
        report = val_orch.generate_validation_report(X_train, y_train, X_val, y_val)
        self._validation_report_view.display_validation_report(report)
        self._update_status({"phase": "ValidationReport"})

        if not self._testing_mode:
            self._stop(
                f"BPMN: DATA SCIENTIST: CHECK VALIDATION RESULTS — "
                f"inspect {self._validation_report_path}. "
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
        decision_text = f"selected model index {best_model_index}" if best_model_index != 0 else "rejected all models"
        self._log_event("ValidationReport", decision_text)
        print(f"[Orchestrator] IS THERE A VALID CLASSIFIER? → index={best_model_index}")

        if best_model_index == 0:
            iteration = self._status.get("iteration", 0) + 1
            if iteration >= self._max_outer_iterations:
                self._finalize_log("rejected report")
                print(
                    f"[Orchestrator] Max outer iterations "
                    f"({self._max_outer_iterations}) reached — saving rejected report."
                )
                self._comm.save_rejected_report(self._testing_report_path)
                self._reset_status()
                return
            print(
                f"[Orchestrator] No valid classifier — "
                f"retry {iteration}/{self._max_outer_iterations}."
            )
            self._update_status({"phase": "Ready", "iteration": iteration})
            self._execute_development()
            return

        classifier_data = self._retrieve_classifier_data(best_model_index)
        if classifier_data is None:
            print(f"[Orchestrator] Model index {best_model_index} is not valid.")
            if not self._testing_mode:
                self._stop(f"Choose a valid index from {self._validation_report_path}.")
            else:
                sys.exit(1)

        print(f"[Orchestrator] Valid classifier found: {classifier_data}")
        self._update_status({"phase": "Testing", "best_classifier_data": classifier_data})
        self._execute_development()

    def generate_test_report(self) -> None:
        """
        BPMN Tasks:
          • GENERATE TEST REPORT
          • DATA SCIENTIST: CHECK TEST RESULTS
        """
        print("[Orchestrator] GENERATE TEST REPORT …")
        best_data  = self._status["best_classifier_data"]
        cl_id      = best_data["index"]
        model_path = os.path.join(self._classifier_folder, f"model_{cl_id}.sav")

        X_test, y_test = self._get_frames("test_set")

        test_orch = TestingOrchestrator(
            report_path=self._testing_report_path,
            generalization_threshold=self._generalization_threshold,
        )
        report = test_orch.test_classifier(model_path, best_data, X_test, y_test)
        self._testing_report_view.display_training_report(report)
        self._update_status({"phase": "Results"})

        if not self._testing_mode:
            self._stop(
                f"BPMN: DATA SCIENTIST: CHECK TEST RESULTS — "
                f"inspect {self._testing_report_path}. "
                f"Set 'approved': true to accept, false to reject."
            )
        else:
            self._execute_development()

    def test_passed(self) -> None:
        """
        BPMN Gateway: TEST PASSED?
            NO  → save rejected report, reset to IDLE
            YES → send classifier to production, reset to IDLE
        """
        approved = self._get_user_input().get("approved", False)
        self._log_event("Results", f"Final approval: {approved}")
        best_data = self._status["best_classifier_data"]
        cl_id = best_data["index"]
        model_path = os.path.join(self._classifier_folder, f"model_{cl_id}.sav")

        if approved:
            print("\n" + "!" * 60)
            print("[Orchestrator] SUCCESS: CLASSIFIER SENT TO PRODUCTION.")
            print("!" * 60 + "\n")
            self._comm.send_classifier(model_path)
            self._finalize_log("classifier")
            self._reset_status()
            
        else:
            print("\n[Orchestrator] TEST REJECTED: Saving report and resetting to IDLE.")
            self._comm.save_rejected_report(self._testing_report_path)
            self._finalize_log("testing report")
            self._reset_status()
           
