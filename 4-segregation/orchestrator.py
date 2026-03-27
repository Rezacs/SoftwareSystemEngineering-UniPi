from common.json_io import JsonIO
from segregation import (
    BALANCING_REPORT_PATH,
    CALIBRATION_SETS_PATH,
    CONFIG_PATH,
    COVERAGE_REPORT_PATH,
    PREPARED_SESSIONS_STORE_PATH,
    PREPARED_SESSION_PATH,
)
from segregation.prepared_session_controller import PreparedSessionController
from segregation.learning_sets_controller import LearningSetsController
from segregation.check_class_balancing import CheckClassBalancing
from segregation.check_input_coverage import CheckInputCoverage


class SegregationSystemOrchestrator:
    def __init__(self):
        self.session_controller = PreparedSessionController()
        self.learning_sets_controller = LearningSetsController()
        self.balancing_checker = CheckClassBalancing()
        self.coverage_checker = CheckInputCoverage()

    def run(
        self,
        input_path=PREPARED_SESSION_PATH,
        storage_path=PREPARED_SESSIONS_STORE_PATH,
        learning_sets_path=CALIBRATION_SETS_PATH,
        balancing_report_path=BALANCING_REPORT_PATH,
        coverage_report_path=COVERAGE_REPORT_PATH,
        config_path=CONFIG_PATH
    ):
        config = JsonIO.load(config_path)
        prepared_session = self.session_controller.receive(input_path)
        stored_sessions = self.session_controller.store(prepared_session, storage_path)

        if len(stored_sessions) < config["sufficientSessionNumber"]:
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
        JsonIO.save(balancing_report_path, balancing_report)

        if not balancing_report["balanced"]:
            return {
                "status": "classes_not_balanced",
                "balancing_report": balancing_report
            }

        statistics = self.coverage_checker.retrieveStatistics(stored_sessions)
        coverage_report = self.coverage_checker.generatePlotData(
            statistics,
            config["coverageThreshold"]
        )
        JsonIO.save(coverage_report_path, coverage_report)

        if not coverage_report["all_features_covered"]:
            return {
                "status": "coverage_not_satisfied",
                "balancing_report": balancing_report,
                "coverage_report": coverage_report
            }

        learning_sets = self.learning_sets_controller.generateCalibrationSets(
            stored_sessions
        )
        self.learning_sets_controller.sendCalibrationSets(
            learning_sets,
            learning_sets_path
        )

        return {
            "status": "calibration_sets_sent",
            "balancing_report": balancing_report,
            "coverage_report": coverage_report,
            "learning_sets": learning_sets
        }
