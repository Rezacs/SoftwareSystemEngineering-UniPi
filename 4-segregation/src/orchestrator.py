"""Coordinates the Segregation System workflow, including storage, checks, stop-and-go decisions, and final set generation."""

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
    def __init__(self):
        self.session_repository = SessionRepository()
        self.data_extractor = DataExtractor()
        self.calibration_set_provider = CalibrationSetProvider()
        self.balancing_checker = CheckClassBalancing()
        self.coverage_checker = CheckInputCoverage()
        self.view_balancing = ViewBalancing()
        self.view_coverage = ViewCoverage()

    def load_state(self, path: str) -> dict:
        try:
            return JsonIO.load(path)
        except FileNotFoundError:
            return {"phase": "idle"}

    def save_state(self, phase: str, path: str, **extra_fields) -> dict:
        state = {"phase": phase, **extra_fields}
        JsonIO.save(path, state)
        return state

    def load_decision(self, path: str) -> Optional[dict]:
        try:
            decision = JsonIO.load(path)
        except FileNotFoundError:
            return None

        return decision if isinstance(decision, dict) else None

    def run(
        self,
        segregation_db_path=SEGREGATION_DB_PATH,
        calibration_set_output_path=CALIBRATION_SET_OUTPUT_PATH,
        balancing_report_output_path=BALANCING_REPORT_OUTPUT_PATH,
        balancing_plot_output_path=BALANCING_PLOT_OUTPUT_PATH,
        coverage_report_output_path=COVERAGE_REPORT_OUTPUT_PATH,
        coverage_plot_output_path=COVERAGE_PLOT_OUTPUT_PATH,
        config_path=CONFIG_PATH,
        workflow_state_path=SEGREGATION_WORKFLOW_STATE_PATH,
        balancing_report_decision_path=BALANCING_REPORT_DECISION_PATH,
        coverage_report_decision_path=COVERAGE_REPORT_DECISION_PATH,
    ):
        config = JsonIO.load(config_path)
        self.session_repository.initialize(segregation_db_path)
        state = self.load_state(workflow_state_path)

        if state["phase"] == "waiting_balancing_decision":
            balancing_decision = self.load_decision(
                balancing_report_decision_path
            )
            if balancing_decision is None:
                return {
                    "status": "waiting_balancing_decision",
                    "state": state,
                    "decision_path": balancing_report_decision_path,
                    "report_path": balancing_report_output_path
                }

            if not balancing_decision.get("approved", False):
                self.session_repository.mark_all_to_process(segregation_db_path)
                self.save_state(
                    "idle",
                    workflow_state_path,
                    balancing_decision=balancing_decision
                )
                return {
                    "status": "balancing_rejected",
                    "balancing_decision": balancing_decision,
                    "report_path": balancing_report_output_path
                }

            feature_map = self.data_extractor.extract_features(segregation_db_path)
            statistics = self.coverage_checker.retrieveStatistics(feature_map)
            coverage_report = self.coverage_checker.generatePlotData(
                statistics,
                config["coverageThreshold"]
            )
            JsonIO.save(coverage_report_output_path, coverage_report)
            self.view_coverage.showPlot(coverage_report, coverage_plot_output_path)
            self.save_state("waiting_coverage_decision", workflow_state_path)
            return {
                "status": "coverage_report_generated",
                "coverage_report": coverage_report,
                "report_path": coverage_report_output_path,
                "plot_path": coverage_plot_output_path,
                "decision_path": coverage_report_decision_path
            }

        if state["phase"] == "waiting_coverage_decision":
            coverage_decision = self.load_decision(
                coverage_report_decision_path
            )
            if coverage_decision is None:
                return {
                    "status": "waiting_coverage_decision",
                    "state": state,
                    "decision_path": coverage_report_decision_path,
                    "report_path": coverage_report_output_path
                }

            if not coverage_decision.get("approved", False):
                self.session_repository.mark_all_to_process(segregation_db_path)
                self.save_state(
                    "idle",
                    workflow_state_path,
                    coverage_decision=coverage_decision
                )
                return {
                    "status": "coverage_rejected",
                    "coverage_decision": coverage_decision,
                    "report_path": coverage_report_output_path
                }

            active_sessions = self.data_extractor.extract_all(segregation_db_path)
            calibration_set = self.calibration_set_provider.generateCalibrationSets(
                active_sessions
            )
            self.calibration_set_provider.sendCalibrationSets(
                calibration_set,
                calibration_set_output_path
            )
            self.session_repository.delete_processed_sessions(segregation_db_path)
            self.session_repository.promote_pending_sessions(segregation_db_path)
            self.save_state("completed", workflow_state_path)
            return {
                "status": "calibration_sets_sent",
                "calibration_set": calibration_set,
                "output_path": calibration_set_output_path
            }

        active_sessions_count = self.session_repository.sessions_count(
            segregation_db_path
        )
        if active_sessions_count < config["sufficientSessionNumber"]:
            self.save_state(
                "sessions_not_sufficient",
                workflow_state_path,
                stored_sessions=active_sessions_count,
                required_sessions=config["sufficientSessionNumber"]
            )
            return {
                "status": "sessions_not_sufficient",
                "stored_sessions": active_sessions_count,
                "required_sessions": config["sufficientSessionNumber"]
            }

        active_sessions = self.session_repository.receive(segregation_db_path)
        labels = self.balancing_checker.retrieveLabels(
            self.data_extractor.extract_labels(segregation_db_path)
        )
        balancing_report = self.balancing_checker.generatePlotData(
            labels,
            config["balancingTolerance"]
        )
        JsonIO.save(balancing_report_output_path, balancing_report)
        self.view_balancing.showPlot(balancing_report, balancing_plot_output_path)
        self.save_state(
            "waiting_balancing_decision",
            workflow_state_path,
            latest_session_id=(
                active_sessions[-1].get("session_id")
                if active_sessions
                else None
            )
        )

        return {
            "status": "balancing_report_generated",
            "balancing_report": balancing_report,
            "report_path": balancing_report_output_path,
            "plot_path": balancing_plot_output_path,
            "decision_path": balancing_report_decision_path
        }
