"""Coordinates the Segregation System workflow, including storage, checks, stop-and-go decisions, and final set generation."""

from datetime import datetime, timezone
import random
from typing import Optional

from .utils.json_io import JsonIO
from . import (
    BALANCING_REPORT_DECISION_PATH,
    BALANCING_REPORT_OUTPUT_PATH,
    BALANCING_PLOT_OUTPUT_PATH,
    CALIBRATION_SET_OUTPUT_PATH,
    CONFIG_PATH,
    COVERAGE_REPORT_DECISION_PATH,
    COVERAGE_REPORT_OUTPUT_PATH,
    COVERAGE_PLOT_OUTPUT_PATH,
    SEGREGATION_LOG_PATH,
    SEGREGATION_DB_PATH,
    SEGREGATION_WORKFLOW_STATE_PATH,
)
from .data_extractor import DataExtractor
from .session_repository import SessionRepository
from .calibration_set_provider import CalibrationSetProvider
from .check_class_balancing import CheckClassBalancing
from .check_input_coverage import CheckInputCoverage
from .view_balancing import ViewBalancing
from .view_coverage import ViewCoverage


class SegregationSystemOrchestrator:
    # S1: from input reception to sufficient-sessions check
    SUBPROCESS_1 = "S1"
    # S2: from passed sufficient-sessions check to class-balancing decision
    SUBPROCESS_2 = "S2"
    # S3: from passed class-balancing check to coverage decision
    SUBPROCESS_3 = "S3"
    # S4: from passed coverage check to output (calibration set) sent
    SUBPROCESS_4 = "S4"
    PROCESS_ORDER = [SUBPROCESS_1, SUBPROCESS_2, SUBPROCESS_3, SUBPROCESS_4]

    def __init__(self, testing_mode: bool = False):
        self.session_repository = SessionRepository()
        self.data_extractor = DataExtractor()
        self.calibration_set_provider = CalibrationSetProvider()
        self.balancing_checker = CheckClassBalancing()
        self.coverage_checker = CheckInputCoverage()
        self.view_balancing = ViewBalancing()
        self.view_coverage = ViewCoverage()
        self.testing_mode = testing_mode

    def load_state(self, path: str) -> dict:
        try:
            return JsonIO.load(path)
        except FileNotFoundError:
            return {"phase": "idle"}

    def save_state(self, phase: str, path: str, **extra_fields) -> dict:
        state = {"phase": phase, **extra_fields}
        JsonIO.save(path, state)
        return state

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _load_segregation_log(self) -> dict:
        try:
            current_log = JsonIO.load(self._paths["segregation_log"])
            return current_log if isinstance(current_log, dict) else {}
        except (FileNotFoundError, ValueError, TypeError):
            return {}

    def _save_segregation_log(self, segregation_log: dict) -> None:
        JsonIO.save(self._paths["segregation_log"], segregation_log)

    def _get_latest_session_key(self, segregation_log: dict) -> Optional[str]:
        keys = sorted(segregation_log.keys(), reverse=True)
        return keys[0] if keys else None

    def _get_or_create_session_processes(
        self,
        segregation_log: dict,
        session_key: Optional[str],
        create_if_missing: bool,
    ) -> tuple[Optional[str], Optional[list], bool]:
        if session_key and session_key in segregation_log and isinstance(segregation_log[session_key], list):
            return session_key, segregation_log[session_key], False

        if session_key and create_if_missing:
            segregation_log[session_key] = []
            return session_key, segregation_log[session_key], True

        if not create_if_missing:
            return None, None, False

        new_session_key = self._utc_now_iso()
        segregation_log[new_session_key] = []
        return new_session_key, segregation_log[new_session_key], True

    def _ensure_subprocess(self, session_processes: list, subprocess_name: str) -> dict:
        for process_entry in session_processes:
            if process_entry.get("process") == subprocess_name:
                return process_entry

        process_entry = {
            "process": subprocess_name,
            "timestamp inizio": self._utc_now_iso(),
            "timestamp fine": None,
            "outcome": None,
        }
        session_processes.append(process_entry)
        return process_entry

    def _set_subprocess_outcome(self, process_entry: dict, outcome: str) -> None:
        process_entry["outcome"] = outcome

    def _complete_subprocess(self, process_entry: dict, outcome: str) -> None:
        process_entry["outcome"] = outcome
        if process_entry.get("timestamp fine") is None:
            process_entry["timestamp fine"] = self._utc_now_iso()

    def _trim_following_processes(self, session_processes: list, process_name: str) -> None:
        if process_name not in self.PROCESS_ORDER:
            return
        keep_set = set(self.PROCESS_ORDER[: self.PROCESS_ORDER.index(process_name) + 1])
        session_processes[:] = [
            process_entry
            for process_entry in session_processes
            if process_entry.get("process") in keep_set
        ]

    def reset_state(self, path: str = SEGREGATION_WORKFLOW_STATE_PATH) -> None:
        """Reset workflow state to idle for a new cycle."""
        self.save_state("idle", path)

    def load_decision(self, path: str) -> Optional[dict]:
        try:
            decision = JsonIO.load(path)
        except FileNotFoundError:
            return None

        return decision if isinstance(decision, dict) else None

    def _simulate_decision(self, decision_type: str) -> dict:
        """
        Simulate user decision in testing mode with specified acceptance rates.
        
        Args:
            decision_type: 'balancing' or 'coverage'
        
        Returns:
            Decision dict with 70% chance of approval, 30% rejection
        """
        # 70% acceptance rate for both checks
        approved = random.random() < 0.70
        decision = {
            "approved": approved,
            "simulated": True,
            "decision_type": decision_type
        }
        print(f"[Orchestrator] Simulated {decision_type} decision: {'APPROVED' if approved else 'REJECTED'} (Testing mode)")
        return decision

    def _stop_and_ask(self, message: str, decision_path: str, report_path: str, plot_path: str = None) -> None:
        """
        Stop execution and wait for user decision in Stop&Go mode.
        In testing mode, simulate the decision automatically.
        
        Args:
            message: Message to display to user
            decision_path: Path to decision file
            report_path: Path to report file
            plot_path: Path to plot file (optional)
        """
        print(f"\n[Orchestrator] {message}")
        print(f"  → Report: {report_path}")
        if plot_path:
            print(f"  → Plot: {plot_path}")
        print(f"  → Decision file: {decision_path}")
        
        if not self.testing_mode:
            print("\n  Please review the report and update the decision file.")
            print("  Then run the system again to continue.")
            # In Stop&Go mode, we exit and wait for the user to manually continue
            return
        else:
            # In testing mode, we simulate the decision automatically
            print("  (Testing mode: simulating decision automatically)")
            # Decision will be simulated in the next run() call

    def run(
        self,
        segregation_db_path=SEGREGATION_DB_PATH,
        calibration_set_output_path=CALIBRATION_SET_OUTPUT_PATH,
        balancing_report_output_path=BALANCING_REPORT_OUTPUT_PATH,
        balancing_plot_output_path=BALANCING_PLOT_OUTPUT_PATH,
        coverage_report_output_path=COVERAGE_REPORT_OUTPUT_PATH,
        coverage_plot_output_path=COVERAGE_PLOT_OUTPUT_PATH,
        segregation_log_path=SEGREGATION_LOG_PATH,
        config_path=CONFIG_PATH,
        workflow_state_path=SEGREGATION_WORKFLOW_STATE_PATH,
        balancing_report_decision_path=BALANCING_REPORT_DECISION_PATH,
        coverage_report_decision_path=COVERAGE_REPORT_DECISION_PATH,
    ):
        """
        Main entry point for the segregation workflow.
        Executes the workflow based on current state and mode (Stop&Go or Testing).
        """
        config = JsonIO.load(config_path)
        self.session_repository.initialize(segregation_db_path)
        
        # Store paths for use in helper methods
        self._paths = {
            "segregation_db": segregation_db_path,
            "calibration_set_output": calibration_set_output_path,
            "balancing_report_output": balancing_report_output_path,
            "balancing_plot_output": balancing_plot_output_path,
            "coverage_report_output": coverage_report_output_path,
            "coverage_plot_output": coverage_plot_output_path,
            "segregation_log": segregation_log_path,
            "workflow_state": workflow_state_path,
            "balancing_decision": balancing_report_decision_path,
            "coverage_decision": coverage_report_decision_path,
        }
        self._config = config
        
        # Execute the workflow based on current phase
        return self._execute_segregation()
    
    def _execute_segregation(self):
        """Routes current phase to its handler."""
        state = self.load_state(self._paths["workflow_state"])
        phase = state["phase"]
        
        dispatch = {
            "idle": self._handle_idle,
            "sessions_not_sufficient": self._handle_idle,  # Treat as idle
            "waiting_balancing_decision": self._handle_balancing_decision,
            "waiting_coverage_decision": self._handle_coverage_decision,
            "completed": self._handle_completed,
        }
        
        handler = dispatch.get(phase, self._handle_idle)
        return handler()
    
    def _handle_idle(self):
        """Check if we have sufficient sessions and generate balancing report."""
        state = self.load_state(self._paths["workflow_state"])
        active_sessions_count = self.session_repository.sessions_count(
            self._paths["segregation_db"]
        )
        segregation_log = self._load_segregation_log()
        state_session_key = state.get("session_log_key")

        can_create_session = active_sessions_count > 0
        session_key, session_processes, is_new_session = self._get_or_create_session_processes(
            segregation_log,
            session_key=state_session_key,
            create_if_missing=can_create_session,
        )

        if session_processes is not None:
            self._ensure_subprocess(session_processes, self.SUBPROCESS_1)
        
        if active_sessions_count < self._config["sufficientSessionNumber"]:
            if session_processes is not None:
                subprocess_1 = self._ensure_subprocess(session_processes, self.SUBPROCESS_1)
                self._set_subprocess_outcome(subprocess_1, "sessions not sufficient")
                if subprocess_1.get("timestamp fine") is None:
                    subprocess_1["timestamp fine"] = self._utc_now_iso()
                self._trim_following_processes(session_processes, self.SUBPROCESS_1)
                self._save_segregation_log(segregation_log)

            # Negative S1 outcome closes the current session; next loop starts a new one.
            self.reset_state(self._paths["workflow_state"])
            return {
                "status": "sessions_not_sufficient",
                "stored_sessions": active_sessions_count,
                "required_sessions": self._config["sufficientSessionNumber"]
            }

        if session_processes is not None:
            subprocess_1 = self._ensure_subprocess(session_processes, self.SUBPROCESS_1)
            self._complete_subprocess(subprocess_1, "sessions sufficient")

            self._ensure_subprocess(session_processes, self.SUBPROCESS_2)
        
        # Generate balancing report
        print("[Orchestrator] Generating balancing report...")
        active_sessions = self.session_repository.receive(self._paths["segregation_db"])
        labels = self.balancing_checker.retrieveLabels(
            self.data_extractor.extract_labels(self._paths["segregation_db"])
        )
        balancing_report = self.balancing_checker.generatePlotData(
            labels,
            self._config["balancingTolerance"]
        )
        JsonIO.save(self._paths["balancing_report_output"], balancing_report)
        self.view_balancing.showPlot(balancing_report, self._paths["balancing_plot_output"])
        if session_processes is not None:
            self._save_segregation_log(segregation_log)

        self.save_state(
            "waiting_balancing_decision",
            self._paths["workflow_state"],
            latest_session_id=(
                active_sessions[-1].get("session_id")
                if active_sessions
                else None
            ),
            session_log_key=session_key,
        )
        
        self._stop_and_ask(
            "BALANCING REPORT GENERATED — Review and decide",
            self._paths["balancing_decision"],
            self._paths["balancing_report_output"],
            self._paths["balancing_plot_output"]
        )
        
        if self.testing_mode:
            # Continue automatically in testing mode
            return self._execute_segregation()
        
        return {
            "status": "balancing_report_generated",
            "balancing_report": balancing_report,
            "report_path": self._paths["balancing_report_output"],
            "plot_path": self._paths["balancing_plot_output"],
            "decision_path": self._paths["balancing_decision"]
        }
    
    def _handle_balancing_decision(self):
        """Process balancing decision and proceed accordingly."""
        state = self.load_state(self._paths["workflow_state"])
        segregation_log = self._load_segregation_log()
        session_key = state.get("session_log_key")
        session_processes = segregation_log.get(session_key) if session_key else None

        # In testing mode, always simulate decision (don't read file)
        if self.testing_mode:
            balancing_decision = self._simulate_decision("balancing")
            JsonIO.save(self._paths["balancing_decision"], balancing_decision)
        else:
            # In stop&go mode, read decision from file
            balancing_decision = self.load_decision(self._paths["balancing_decision"])
        
        if balancing_decision is None:
            print("[Orchestrator] Waiting for balancing decision...")
            return {
                "status": "waiting_balancing_decision",
                "decision_path": self._paths["balancing_decision"],
                "report_path": self._paths["balancing_report_output"]
            }
        
        if not balancing_decision.get("approved", False):
            print("[Orchestrator] Balancing REJECTED — Resetting to idle")
            if isinstance(session_processes, list):
                subprocess_2 = self._ensure_subprocess(session_processes, self.SUBPROCESS_2)
                self._complete_subprocess(subprocess_2, "classes not balanced")
                self._trim_following_processes(session_processes, self.SUBPROCESS_2)
                self._save_segregation_log(segregation_log)

            self.session_repository.mark_all_to_process(self._paths["segregation_db"])
            self.reset_state(self._paths["workflow_state"])
            
            if self.testing_mode:
                # Auto-reset and wait for new data
                print("[Orchestrator] Auto-reset complete. Ready for new sessions.")
            
            return {
                "status": "balancing_rejected",
                "balancing_decision": balancing_decision,
                "report_path": self._paths["balancing_report_output"]
            }
        
        # Balancing approved - generate coverage report
        print("[Orchestrator] Balancing APPROVED — Generating coverage report...")
        if isinstance(session_processes, list):
            subprocess_2 = self._ensure_subprocess(session_processes, self.SUBPROCESS_2)
            self._complete_subprocess(subprocess_2, "classes balanced")

            self._ensure_subprocess(session_processes, self.SUBPROCESS_3)

        feature_map = self.data_extractor.extract_features(self._paths["segregation_db"])
        statistics = self.coverage_checker.retrieveStatistics(feature_map)
        coverage_report = self.coverage_checker.generatePlotData(
            statistics,
            self._config["coverageThreshold"]
        )
        JsonIO.save(self._paths["coverage_report_output"], coverage_report)
        self.view_coverage.showPlot(coverage_report, self._paths["coverage_plot_output"])

        if isinstance(session_processes, list):
            self._save_segregation_log(segregation_log)

        self.save_state(
            "waiting_coverage_decision",
            self._paths["workflow_state"],
            session_log_key=session_key,
        )
        
        self._stop_and_ask(
            "COVERAGE REPORT GENERATED — Review and decide",
            self._paths["coverage_decision"],
            self._paths["coverage_report_output"],
            self._paths["coverage_plot_output"]
        )
        
        if self.testing_mode:
            # Continue automatically in testing mode
            return self._execute_segregation()
        
        return {
            "status": "coverage_report_generated",
            "coverage_report": coverage_report,
            "report_path": self._paths["coverage_report_output"],
            "plot_path": self._paths["coverage_plot_output"],
            "decision_path": self._paths["coverage_decision"]
        }
    
    def _handle_coverage_decision(self):
        """Process coverage decision and finalize or reject."""
        state = self.load_state(self._paths["workflow_state"])
        segregation_log = self._load_segregation_log()
        session_key = state.get("session_log_key")
        session_processes = segregation_log.get(session_key) if session_key else None

        # In testing mode, always simulate decision (don't read file)
        if self.testing_mode:
            coverage_decision = self._simulate_decision("coverage")
            JsonIO.save(self._paths["coverage_decision"], coverage_decision)
        else:
            # In stop&go mode, read decision from file
            coverage_decision = self.load_decision(self._paths["coverage_decision"])
        
        if coverage_decision is None:
            print("[Orchestrator] Waiting for coverage decision...")
            return {
                "status": "waiting_coverage_decision",
                "decision_path": self._paths["coverage_decision"],
                "report_path": self._paths["coverage_report_output"]
            }
        
        if not coverage_decision.get("approved", False):
            print("[Orchestrator] Coverage REJECTED — Resetting to idle")
            if isinstance(session_processes, list):
                subprocess_3 = self._ensure_subprocess(session_processes, self.SUBPROCESS_3)
                self._complete_subprocess(subprocess_3, "coverage not satisfied")
                self._trim_following_processes(session_processes, self.SUBPROCESS_3)
                self._save_segregation_log(segregation_log)

            self.session_repository.mark_all_to_process(self._paths["segregation_db"])
            self.reset_state(self._paths["workflow_state"])
            
            if self.testing_mode:
                # Auto-reset and wait for new data
                print("[Orchestrator] Auto-reset complete. Ready for new sessions.")
            
            return {
                "status": "coverage_rejected",
                "coverage_decision": coverage_decision,
                "report_path": self._paths["coverage_report_output"]
            }
        
        # Coverage approved - generate calibration set
        print("[Orchestrator] Coverage APPROVED — Generating calibration set...")
        if isinstance(session_processes, list):
            subprocess_3 = self._ensure_subprocess(session_processes, self.SUBPROCESS_3)
            self._complete_subprocess(subprocess_3, "coverage satisfied")

            self._ensure_subprocess(session_processes, self.SUBPROCESS_4)

        active_sessions = self.data_extractor.extract_all(self._paths["segregation_db"])
        calibration_set = self.calibration_set_provider.generateCalibrationSets(
            active_sessions
        )
        self.calibration_set_provider.sendCalibrationSets(
            calibration_set,
            self._paths["calibration_set_output"]
        )
        self.session_repository.delete_processed_sessions(self._paths["segregation_db"])
        self.session_repository.promote_pending_sessions(self._paths["segregation_db"])

        if isinstance(session_processes, list):
            subprocess_4 = self._ensure_subprocess(session_processes, self.SUBPROCESS_4)
            self._complete_subprocess(subprocess_4, "output sent")
            self._save_segregation_log(segregation_log)

        self.save_state("completed", self._paths["workflow_state"])
        
        print("[Orchestrator] Calibration set sent successfully!")
        
        if self.testing_mode:
            # Auto-reset after completion
            print("[Orchestrator] Workflow complete. Resetting for next cycle...")
            self.reset_state(self._paths["workflow_state"])
        
        return {
            "status": "calibration_sets_sent",
            "calibration_set": calibration_set,
            "output_path": self._paths["calibration_set_output"]
        }
    
    def _handle_completed(self):
        """Handle completed state - reset for next cycle."""
        print("[Orchestrator] Workflow already completed. Resetting...")
        self.reset_state(self._paths["workflow_state"])
        return {
            "status": "reset_complete",
            "message": "Ready for new sessions"
        }
