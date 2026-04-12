"""Non-resilience tests for the Segregation System based on S1-S5 scenarios.

Usage:
  1) Start segregation/main.py in another terminal.
  2) Run this script.

The script sends crafted prepared sessions to /prepared-sessions and prints:
- HTTP responses
- observed DB effects
- workflow/report snapshots when available
"""

import json
import sqlite3
import time
from pathlib import Path

import requests

from src import (
    BALANCING_REPORT_ENDPOINT,
    BALANCING_REPORT_OUTPUT_PATH,
    CONFIG_PATH,
    COVERAGE_REPORT_ENDPOINT,
    COVERAGE_REPORT_OUTPUT_PATH,
    HEALTH_ENDPOINT,
    PREPARED_SESSIONS_ENDPOINT,
    SEGREGATION_DB_PATH,
    SEGREGATION_WORKFLOW_STATE_PATH,
    WORKFLOW_STATE_ENDPOINT,
)


REPO_ROOT = Path(__file__).resolve().parent.parent


# Load segregation system network config from repository config.
def load_config() -> dict:
    with Path(CONFIG_PATH).open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


# Build API base URL (for example http://127.0.0.1:5003).
def build_base_url(config: dict) -> str:
    return f"http://{config['segregationSystemIpAddress']}:{config['segregationSystemPort']}"


# Send one prepared session to segregation ingestion endpoint.
def post_prepared_session(base_url: str, payload: dict) -> tuple[int, str]:
    response = requests.post(
        f"{base_url}{PREPARED_SESSIONS_ENDPOINT}",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=5,
    )
    return response.status_code, response.text


# Read JSON response from a GET endpoint; return None if unavailable.
def get_json_or_none(base_url: str, endpoint: str) -> dict | None:
    try:
        response = requests.get(f"{base_url}{endpoint}", timeout=5)
        if not response.ok:
            return None
        return response.json()
    except requests.RequestException:
        return None


# Count rows in segregation SQLite DB, optionally filtered by session_id.
def count_db_rows(session_id: str | None = None) -> int:
    db_path = Path(SEGREGATION_DB_PATH)
    if not db_path.exists():
        return 0

    query = "SELECT COUNT(*) FROM prepared_sessions"
    params: tuple = ()
    if session_id is not None:
        query += " WHERE session_id = ?"
        params = (session_id,)

    with sqlite3.connect(db_path) as connection:
        return int(connection.execute(query, params).fetchone()[0])


# Remove runtime artifacts so each scenario starts from a clean state.
def reset_local_runtime_files() -> None:
    for path_str in [
        SEGREGATION_DB_PATH,
        SEGREGATION_WORKFLOW_STATE_PATH,
        BALANCING_REPORT_OUTPUT_PATH,
        COVERAGE_REPORT_OUTPUT_PATH,
    ]:
        path = Path(path_str)
        if path.exists():
            path.unlink()


# Build a valid prepared session payload.
def make_session(
    session_id: str,
    player_id: int,
    label: int,
    skill_overall: float,
    social_influence_score: float,
    injuries_impact_score: float,
) -> dict:
    return {
        "session_id": session_id,
        "player_id": player_id,
        "label": label,
        "skill_overall": skill_overall,
        "social_influence_score": social_influence_score,
        "injuries_impact_score": injuries_impact_score,
    }


# Send a list of prepared sessions with a short pause between requests.
def send_batch(base_url: str, sessions: list[dict], pause_seconds: float = 0.1) -> None:
    for session in sessions:
        status, body = post_prepared_session(base_url, session)
        print(f"  -> {session['session_id']} HTTP {status}: {body}")
        time.sleep(pause_seconds)


# Poll workflow/report endpoints for a short period and return latest snapshot.
def wait_for_reports(base_url: str, timeout_seconds: int = 12) -> tuple[dict | None, dict | None, dict | None]:
    deadline = time.time() + timeout_seconds
    workflow = None
    balancing = None
    coverage = None

    while time.time() < deadline:
        workflow = get_json_or_none(base_url, WORKFLOW_STATE_ENDPOINT)
        balancing = get_json_or_none(base_url, BALANCING_REPORT_ENDPOINT)
        coverage = get_json_or_none(base_url, COVERAGE_REPORT_ENDPOINT)

        if balancing is not None or coverage is not None:
            break

        time.sleep(1)

    return workflow, balancing, coverage


# S1: wrong schema should be rejected at API level (HTTP 400), not stored.
def case_s1_wrong_schema(base_url: str) -> None:
    print("\n--- S1: Wrong prepared session schema (expected discard) ---")
    reset_local_runtime_files()

    wrong_payload = {
        "session_id": "s1-invalid-001",
        "player_id": 1001,
        "label": 3,
        # Missing skill_overall on purpose
        "social_influence_score": 0.4,
        "injuries_impact_score": 0.3,
    }

    before = count_db_rows()
    status, body = post_prepared_session(base_url, wrong_payload)
    after = count_db_rows()

    print(f"HTTP {status}: {body}")
    print(f"DB rows before={before}, after={after}")


# S2: duplicate UUID should keep first session and discard the second one.
def case_s2_duplicate_uuid(base_url: str) -> None:
    print("\n--- S2: Duplicate UUID sessions (expected keep first only) ---")
    reset_local_runtime_files()

    duplicated_id = "s2-dup-001"
    first = make_session(duplicated_id, 2001, 1, 0.2, 0.6, 0.4)
    second = make_session(duplicated_id, 2002, 5, 0.9, 0.1, 0.1)

    status_1, body_1 = post_prepared_session(base_url, first)
    status_2, body_2 = post_prepared_session(base_url, second)

    total_with_same_id = count_db_rows(duplicated_id)
    print(f"first send  -> HTTP {status_1}: {body_1}")
    print(f"second send -> HTTP {status_2}: {body_2}")
    print(f"rows with session_id='{duplicated_id}': {total_with_same_id}")


# S3: extreme/outlier features are accepted by current schema and processed.
def case_s3_wrong_features_outliers(base_url: str) -> None:
    print("\n--- S3: Wrong features / outliers (expected processed) ---")
    reset_local_runtime_files()

    labels = [1, 2, 3, 4, 5, 1, 2, 3, 4, 5]
    sessions = []
    for idx, label in enumerate(labels, start=1):
        skill = 10_000.0 if idx == 3 else (0.3 + 0.05 * idx)
        social = -9_999.0 if idx == 7 else (0.2 + 0.03 * idx)
        injuries = 5_000.0 if idx == 9 else (0.1 + 0.02 * idx)
        sessions.append(
            make_session(
                session_id=f"s3-outlier-{idx:03d}",
                player_id=3000 + idx,
                label=label,
                skill_overall=skill,
                social_influence_score=social,
                injuries_impact_score=injuries,
            )
        )

    send_batch(base_url, sessions)
    workflow, balancing, coverage = wait_for_reports(base_url)

    print(f"workflow_state: {workflow}")
    print(f"balancing_report approved: {None if balancing is None else balancing.get('approved')}")
    if coverage is None:
        print("coverage_report: not available yet")
    else:
        print(f"coverage_report approved: {coverage.get('approved')}")


# S4: strongly unbalanced labels should fail balancing check.
def case_s4_unbalanced_labels(base_url: str) -> None:
    print("\n--- S4: Unbalanced labels (expected stop at balancing) ---")
    reset_local_runtime_files()

    sessions = []
    for idx in range(1, 11):
        sessions.append(
            make_session(
                session_id=f"s4-unbalanced-{idx:03d}",
                player_id=4000 + idx,
                label=1,
                skill_overall=0.2 + 0.01 * idx,
                social_influence_score=0.3 + 0.01 * idx,
                injuries_impact_score=0.4 + 0.01 * idx,
            )
        )

    send_batch(base_url, sessions)
    workflow, balancing, _ = wait_for_reports(base_url)

    print(f"workflow_state: {workflow}")
    if balancing is None:
        print("balancing_report: not available yet")
    else:
        print(f"balancing_report approved: {balancing.get('approved')}")
        print(f"distribution: {balancing.get('distribution')}")


# S5: constant feature values should fail coverage check after balancing phase.
def case_s5_features_not_distributed(base_url: str) -> None:
    print("\n--- S5: Features not well distributed (expected stop at coverage) ---")
    reset_local_runtime_files()

    labels = [1, 2, 3, 4, 5, 1, 2, 3, 4, 5]
    sessions = []
    for idx, label in enumerate(labels, start=1):
        sessions.append(
            make_session(
                session_id=f"s5-flatfeat-{idx:03d}",
                player_id=5000 + idx,
                label=label,
                skill_overall=0.5,
                social_influence_score=0.5,
                injuries_impact_score=0.5,
            )
        )

    send_batch(base_url, sessions)
    workflow, balancing, coverage = wait_for_reports(base_url)

    print(f"workflow_state: {workflow}")
    print(f"balancing_report approved: {None if balancing is None else balancing.get('approved')}")
    if coverage is None:
        print(
            "coverage_report: not available yet (in Stop&Go mode, approve balancing_decision first)"
        )
    else:
        print(f"coverage_report approved: {coverage.get('approved')}")
        print(f"uncoveredFeatures: {coverage.get('uncoveredFeatures')}")


# Run all non-resilience scenarios in sequence and print observed behavior.
def main() -> None:
    config = load_config()
    base_url = build_base_url(config)

    print("=" * 72)
    print("NON-RESILIENCE TEST — SEGREGATION SYSTEM (S1-S5)")
    print("=" * 72)
    print(f"Base URL: {base_url}")

    health = get_json_or_none(base_url, HEALTH_ENDPOINT)
    if health is None:
        print("Server is not reachable. Start segregation/main.py first.")
        return

    print(f"Health: {health}")

    # Run scenarios in order S1 -> S5.
    case_s1_wrong_schema(base_url)
    case_s2_duplicate_uuid(base_url)
    case_s3_wrong_features_outliers(base_url)
    case_s4_unbalanced_labels(base_url)
    case_s5_features_not_distributed(base_url)

    print("\nDone.")


if __name__ == "__main__":
    main()
