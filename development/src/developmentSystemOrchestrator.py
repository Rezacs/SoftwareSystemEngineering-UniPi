import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
import atexit

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
CONFIG_PATH = REPO_ROOT / "config" / "developmentConfig.json"
LOG_PATH = REPO_ROOT / "logs" / "developmentLog.json"
print(f"[Orchestrator] Loading configuration from: {CONFIG_PATH}")


def _load_config() -> dict:
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(
            f"Configuration file not found: {CONFIG_PATH}\n"
            f"Make sure ../config/developmentConfig.json exists before running."
        )
    with CONFIG_PATH.open("r", encoding="UTF-8") as f:
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
        self._status_file_path       = Path(pth["status_file"])
        self._classifier_folder      = Path(pth["classifier_folder"])
        self._learning_curve_path    = Path(pth["learning_curve"])
        self._validation_report_path = Path(pth["validation_report"])
        self._testing_report_path    = Path(pth["testing_report"])
        self._user_input_path        = Path(pth["user_input"])

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
            listen_host          = net["listen_host"],
            listen_port          = int(net["listen_port"]),
            segregation_ip       = net["segregation_system"]["ip"],
            segregation_port     = int(net["segregation_system"]["port"]),
            production_ip        = net["production_system"]["ip"],
            production_port      = int(net["production_system"]["port"]),
            production_endpoint  = net["production_system"]["endpoint"],
            received_data_path   = pth["received_data"],
            rejected_report_path = pth["rejected_report"],
        )

        # log
        self._log_path    = LOG_PATH
        self._session_key = "current_session"

    # ── status persistence ─────────────────────────────────────────────

    def _default_status(self) -> Dict[str, Any]:
        return {
            "phase":                "Starting",
            "max_iter":             self._default_max_iter,
            "avg_params":           {},
            "best_classifier_data": None,
            "iteration":            0,
            "calibration_done":     False,  # ← add this
        }

    def _load_status(self) -> Dict[str, Any]:
        if self._status_file_path.is_file():
            with self._status_file_path.open("r", encoding="UTF-8") as f:
                return json.load(f)
        return self._default_status()

    def _save_status(self) -> None:
        self._status_file_path.parent.mkdir(parents=True, exist_ok=True)
        with self._status_file_path.open("w", encoding="UTF-8") as f:
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
        if self._user_input_path.is_file():
            try:
                with self._user_input_path.open("r", encoding="UTF-8") as f:
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

        self._user_input_path.parent.mkdir(parents=True, exist_ok=True)
        with self._user_input_path.open("w", encoding="UTF-8") as f:
            json.dump(payload, f, indent="\t")

    def _get_user_input(self) -> dict:
        """
        testing_mode=False → reads user_input.json (human decision)
        testing_mode=True  → simulates decision from report files
        """
        if self._testing_mode:
            return self._simulate_user_input()
        try:
            with self._user_input_path.open("r", encoding="UTF-8") as f:
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
            calibration_done = self._status.get("calibration_done", False)
            if not calibration_done:
                self._update_status({"calibration_done": True})
                return {"max_iter": self._default_max_iter, "good_max_iter": False}
            return {"max_iter": self._default_max_iter, "good_max_iter": True}
        elif phase == "ValidationReport":
            with self._validation_report_path.open("r", encoding="UTF-8") as f:
                report = json.load(f)
            index = next(
                (item["index"] for item in report["best_classifiers"] if item["valid"]), 0
            )
            return {"best_model": index}
        elif phase == "Results":
            with self._testing_report_path.open("r", encoding="UTF-8") as f:
                report = json.load(f)
            return {"approved": report["errors"]["passed"]}
        return {}

    # ── stop&go helper ─────────────────────────────────────────────────

    def _stop(self, message: str) -> None:
        """Stop helper to handle different stopping points in the BPMN."""
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
        with self._validation_report_path.open("r", encoding="UTF-8") as f:
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
        """Construct HyperParameters internally from config."""
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

    # ── logging ────────────────────────────────────────────────────────

    def _now(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _init_log(self) -> None:
        """Initialize the log file and stamp the session beginning."""
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if self._log_path.is_file():
            with self._log_path.open("r", encoding="UTF-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        if self._session_key not in data:
            data[self._session_key] = [{"beginning_ts": self._now()}]
        with self._log_path.open("w", encoding="UTF-8") as f:
            json.dump(data, f, indent="\t")

    def _log_start_event(self, process: str, label: str) -> None:
        """Opens a new event entry with initial_ts; decision and final_ts are filled later."""
        if not self._log_path.is_file():
            self._init_log()
        with self._log_path.open("r+", encoding="UTF-8") as f:
            data = json.load(f)
            event = {
                "process":    process,
                "label":      label,
                "initial_ts": self._now(),
                "final_ts":   None,
                "decision":   None,
            }
            data[self._session_key].append(event)
            f.seek(0)
            json.dump(data, f, indent="\t")
            f.truncate()

    def _log_close_event(self, process: str, decision: str) -> None:
        """Closes the most recent open event for the given process."""
        with self._log_path.open("r+", encoding="UTF-8") as f:
            data = json.load(f)
            for event in reversed(data[self._session_key]):
                if event.get("process") == process and event.get("final_ts") is None:
                    event["final_ts"] = self._now()
                    event["decision"] = decision
                    break
            f.seek(0)
            json.dump(data, f, indent="\t")
            f.truncate()

    def _finalize_log(self, output_type: str) -> None:
        """Finalizes the session: appends output entry and renames key to timestamp."""
        if not self._log_path.is_file():
            return
        with self._log_path.open("r+", encoding="UTF-8") as f:
            data = json.load(f)
            if self._session_key in data:
                session_data = data.pop(self._session_key)
                session_data.append({"output": output_type})
                data[self._now()] = session_data
                f.seek(0)
                json.dump(data, f, indent="\t")
                f.truncate()

    def _emergency_finalize(self) -> None:
        """Fallback finalizer in case the process exits without completing normally."""
        if not self._log_path.is_file():
            return
        with self._log_path.open("r+", encoding="UTF-8") as f:
            data = json.load(f)
            if self._session_key in data:
                session_data = data.pop(self._session_key)
                session_data.append({"output": "interrupted"})
                data[self._now()] = session_data
                f.seek(0)
                json.dump(data, f, indent="\t")
                f.truncate()

    # ── state machine entry point ──────────────────────────────────────

    def run(self, fresh: bool = False) -> None:
        """BPMN start event: CALIBRATION SET RECEIVED."""
        if fresh:
            self._reset_status()

        # always close any leftover session from a previous interrupted run
        self._emergency_finalize()
    
        atexit.register(self._emergency_finalize)

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
        """BPMN Task: SET AVERAGE HYPERPARAMS — D1"""
        self._log_start_event("D1", "set average hyperparams")

        val_orch = ValidationOrchestrator(
            hp_configs=self._hyper_param_configs,
            classifier_folder=self._classifier_folder,
            report_path=self._validation_report_path,
            training_orchestrator=self._make_training_orchestrator(),
            overfitting_threshold=self._overfitting_threshold,
        )
        avg_params = val_orch.retrieve_average_parameters()
        print(f"[Orchestrator] SET AVERAGE HYPERPARAMS: {avg_params}")

        params_str = ", ".join(f"{k}: {v}" for k, v in avg_params.items())
        self._log_close_event("D1", params_str)

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
          • CALIBRATE — D2
          • GENERATE CALIBRATION REPORT
          • DATA SCIENTIST: CHECK CALIBRATION PLOT — D4

        BPMN Gateway: #ITERATIONS FINE?
          NO  → regenerate calibration report with updated max_iter
          YES → advance to generate_validation_report()
        """
        user_input = self._get_user_input()
        good_iter  = user_input.get("good_max_iter", False)

        if not good_iter:
            max_iter = user_input.get("max_iter", self._status["max_iter"])
            self._update_status({"max_iter": max_iter})
            print(f"[Orchestrator] CALIBRATE — {max_iter} epochs …")

            self._log_start_event("D2", "calibrate")

            X_train, y_train = self._get_frames("training_set")
            to = self._make_training_orchestrator()
            params = dict(self._status.get("avg_params", {}))
            params["max_iter"] = max_iter
            to.set_parameters(params)

            plot = to.generate_calibration_report(X_train, y_train, self._learning_curve_path)
            self._learning_plot_view.display_learning_plot(plot)

            self._log_close_event("D2", f"max_iter: {max_iter}")
            self._log_start_event("D4", "check calibration plot")

            if not self._testing_mode:
                self._stop(
                    f"BPMN: DATA SCIENTIST: CHECK CALIBRATION PLOT — "
                    f"inspect {self._learning_curve_path}. "
                    f"Adjust 'max_iter' if needed, then set 'good_max_iter': true."
                )
            else:
                self._execute_development()
        else:
            self._log_close_event("D4", f"approved iterations: {self._status['max_iter']}")
            print(f"[Orchestrator] #ITERATIONS FINE — {self._status['max_iter']} approved.")
            self._update_status({"phase": "Validation"})
            self._execute_development()

    def generate_validation_report(self) -> None:
        """
        BPMN Tasks:
          • SET HYPERPARAMS + GENERATE VALIDATION REPORT — D3
          • DATA SCIENTIST: CHECK VALIDATION RESULTS — D5
        """
        print("[Orchestrator] SET HYPERPARAMS & GENERATE VALIDATION REPORT …")

        self._log_start_event("D3", "generate validation report")

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

        self._log_close_event("D3", f"classifiers evaluated: {len(self._hyper_param_configs)}")
        self._update_status({"phase": "ValidationReport"})
        self._log_start_event("D5", "check validation results")

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
        decision_text    = f"selected model index {best_model_index}" if best_model_index != 0 else "rejected all models"

        self._log_close_event("D5", decision_text)
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
        print("[Orchestrator] GENERATE TEST REPORT …")

        self._log_start_event("D6", "generate test report")

        try:
            best_data  = self._status["best_classifier_data"]
            cl_id      = best_data["index"]
            model_path = self._classifier_folder / f"model_{cl_id}.sav"

            X_test, y_test = self._get_frames("test_set")

            test_orch = TestingOrchestrator(
            report_path=self._testing_report_path,
            generalization_threshold=self._generalization_threshold,
            )
            report = test_orch.test_classifier(model_path, best_data, X_test, y_test)
            self._testing_report_view.display_training_report(report)

            passed = report.result
            score  = report.testing_error
            self._log_close_event("D6", f"passed: {passed}, generalization: {score}")

        except Exception as e:
            self._log_close_event("D6", f"error: {e}")
            raise

        self._update_status({"phase": "Results"})
        self._log_start_event("D7", "check test results")

        if not self._testing_mode:
            self._stop(...)
        else:
            self._execute_development()

    def test_passed(self) -> None:
        """
        BPMN Gateway: TEST PASSED?
            NO  → save rejected report, reset to IDLE
            YES → send classifier to production, reset to IDLE
        """
        approved = self._get_user_input().get("approved", False)

        self._log_close_event("D7", f"Final approval: {approved}")

        best_data  = self._status["best_classifier_data"]
        cl_id      = best_data["index"]
        model_path = self._classifier_folder / f"model_{cl_id}.sav"

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