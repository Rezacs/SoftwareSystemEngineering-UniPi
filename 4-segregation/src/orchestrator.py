from .utils.json_io import JsonIO
from segregation import (
    BALANCING_REPORT_DECISION_PATH,
    BALANCING_REPORT_OUTPUT_PATH,
    CALIBRATION_SET_OUTPUT_PATH,
    CONFIG_PATH,
    COVERAGE_REPORT_DECISION_PATH,
    COVERAGE_REPORT_OUTPUT_PATH,
    PREPARED_SESSION_INPUT_PATH,
    PREPARED_SESSION_REPOSITORY_PATH,
    SEGREGATION_WORKFLOW_STATE_PATH,
)
from segregation.session_repository import SessionRepository
from segregation.calibration_set_provider import CalibrationSetProvider
from segregation.check_class_balancing import CheckClassBalancing
from segregation.check_input_coverage import CheckInputCoverage


class SegregationSystemOrchestrator:
    def __init__(self):
        self.session_repository = SessionRepository()
        self.calibration_set_provider = CalibrationSetProvider()
        self.balancing_checker = CheckClassBalancing()
        self.coverage_checker = CheckInputCoverage()

    def load_state(self, path: str) -> dict:
        try:
            return JsonIO.load(path)
        except FileNotFoundError:
            return {"phase": "idle"}

    def save_state(self, phase: str, path: str, **extra_fields) -> dict:
        state = {"phase": phase, **extra_fields}
        JsonIO.save(path, state)
        return state

    def load_decision(self, path: str) -> dict | None:
        try:
            decision = JsonIO.load(path)
        except FileNotFoundError:
            return None

        return decision if isinstance(decision, dict) else None

    def run(
        self,
        prepared_session_input_path=PREPARED_SESSION_INPUT_PATH,
        prepared_session_repository_path=PREPARED_SESSION_REPOSITORY_PATH,
        calibration_set_output_path=CALIBRATION_SET_OUTPUT_PATH,
        balancing_report_output_path=BALANCING_REPORT_OUTPUT_PATH,
        coverage_report_output_path=COVERAGE_REPORT_OUTPUT_PATH,
        config_path=CONFIG_PATH,
        workflow_state_path=SEGREGATION_WORKFLOW_STATE_PATH,
        balancing_report_decision_path=BALANCING_REPORT_DECISION_PATH,
        coverage_report_decision_path=COVERAGE_REPORT_DECISION_PATH,
    ):
        config = JsonIO.load(config_path)
        state = self.load_state(workflow_state_path)
        stored_sessions = self.session_repository.receiveStored(
            prepared_session_repository_path
        )

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
                self.save_state(
                    "balancing_rejected",
                    workflow_state_path,
                    balancing_decision=balancing_decision
                )
                return {
                    "status": "balancing_rejected",
                    "balancing_decision": balancing_decision,
                    "report_path": balancing_report_output_path
                }

            statistics = self.coverage_checker.retrieveStatistics(stored_sessions)
            coverage_report = self.coverage_checker.generatePlotData(
                statistics,
                config["coverageThreshold"]
            )
            JsonIO.save(coverage_report_output_path, coverage_report)
            self.save_state("waiting_coverage_decision", workflow_state_path)
            return {
                "status": "coverage_report_generated",
                "coverage_report": coverage_report,
                "report_path": coverage_report_output_path,
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
                self.save_state(
                    "coverage_rejected",
                    workflow_state_path,
                    coverage_decision=coverage_decision
                )
                return {
                    "status": "coverage_rejected",
                    "coverage_decision": coverage_decision,
                    "report_path": coverage_report_output_path
                }

            calibration_set = self.calibration_set_provider.generateCalibrationSets(
                stored_sessions
            )
            self.calibration_set_provider.sendCalibrationSets(
                calibration_set,
                calibration_set_output_path
            )
            self.save_state("completed", workflow_state_path)
            return {
                "status": "calibration_sets_sent",
                "calibration_set": calibration_set,
                "output_path": calibration_set_output_path
            }

        prepared_session = self.session_repository.receive(
            prepared_session_input_path
        )
        stored_sessions = self.session_repository.store(
            prepared_session,
            prepared_session_repository_path
        )
        if len(stored_sessions) < config["sufficientSessionNumber"]:
            self.save_state(
                "sessions_not_sufficient",
                workflow_state_path,
                stored_sessions=len(stored_sessions),
                required_sessions=config["sufficientSessionNumber"]
            )
            return {
                "status": "sessions_not_sufficient",
                "stored_sessions": len(stored_sessions),
                "required_sessions": config["sufficientSessionNumber"]
            }

        labels = self.balancing_checker.retrieveLabels(stored_sessions)
        balancing_report = self.balancing_checker.generatePlotData(
            labels,
            config["balancingTolerance"]
        )
        JsonIO.save(balancing_report_output_path, balancing_report)
        self.save_state(
            "waiting_balancing_decision",
            workflow_state_path,
            latest_session_id=prepared_session.get("session_id")
        )

        return {
            "status": "balancing_report_generated",
            "balancing_report": balancing_report,
            "report_path": balancing_report_output_path,
            "decision_path": balancing_report_decision_path
        }
