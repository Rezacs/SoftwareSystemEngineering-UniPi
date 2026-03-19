from common.json_io import JsonIO
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
        input_path="data/outputs/prepared_session.json",
        storage_path="data/outputs/prepared_sessions_store.json",
        learning_sets_path="data/outputs/learning_sets.json",
        balancing_report_path="data/outputs/balancing_report.json",
        coverage_report_path="data/outputs/coverage_report.json"
    ):
        prepared_session = self.session_controller.receive_prepared_session(input_path)

        stored_sessions = self.session_controller.load_existing_sessions(storage_path)
        stored_sessions.append(prepared_session)

        self.session_controller.save_sessions(stored_sessions, storage_path)

        distribution = self.balancing_checker.build_distribution(stored_sessions)
        balancing_report = self.balancing_checker.check_balance(distribution)
        JsonIO.save(balancing_report_path, balancing_report)

        coverage_report = self.coverage_checker.build_coverage_report(stored_sessions)
        JsonIO.save(coverage_report_path, coverage_report)

        learning_sets = self.learning_sets_controller.generate_learning_sets(stored_sessions)
        JsonIO.save(learning_sets_path, learning_sets)

        return {
            "balancing_report": balancing_report,
            "coverage_report": coverage_report,
            "learning_sets": learning_sets
        }