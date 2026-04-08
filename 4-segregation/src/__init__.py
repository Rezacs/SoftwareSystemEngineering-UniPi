"""Defines internal configuration paths used by the Segregation System source code."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parent

CONFIG_PATH = str(REPO_ROOT / "config" / "segregationConfig.json")
HEALTH_ENDPOINT = "/health"
PREPARED_SESSIONS_ENDPOINT = "/prepared-sessions"
WORKFLOW_STATE_ENDPOINT = "/workflow/state"
BALANCING_REPORT_ENDPOINT = "/reports/balancing"
COVERAGE_REPORT_ENDPOINT = "/reports/coverage"
BALANCING_PLOT_ENDPOINT = "/reports/balancing/plot"
COVERAGE_PLOT_ENDPOINT = "/reports/coverage/plot"
CALIBRATION_SET_ENDPOINT = "/calibration-set"
PREPARED_SESSION_INPUT_PATH = str(PROJECT_ROOT / "data" / "input" / "prepared_session.json")
BALANCING_REPORT_DECISION_PATH = str(PROJECT_ROOT / "data" / "input" / "balancing_decision.json")
COVERAGE_REPORT_DECISION_PATH = str(PROJECT_ROOT / "data" / "input" / "coverage_decision.json")
SEGREGATION_DB_PATH = str(PROJECT_ROOT / "data" / "output" / "segregationDB.db")
BALANCING_REPORT_OUTPUT_PATH = str(PROJECT_ROOT / "data" / "output" / "balancing_report.json")
COVERAGE_REPORT_OUTPUT_PATH = str(PROJECT_ROOT / "data" / "output" / "coverage_report.json")
BALANCING_PLOT_OUTPUT_PATH = str(PROJECT_ROOT / "data" / "output" / "balancing_report.png")
COVERAGE_PLOT_OUTPUT_PATH = str(PROJECT_ROOT / "data" / "output" / "coverage_report.png")
CALIBRATION_SET_OUTPUT_PATH = str(PROJECT_ROOT / "data" / "output" / "calibration_set.json")
SEGREGATION_WORKFLOW_STATE_PATH = str(PROJECT_ROOT / "data" / "output" / "segregation_workflow_state.json")
