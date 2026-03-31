"""
Entry point for the Development System.

On startup the user is asked which mode to run:

  [1] Stop&Go (interactive)
        Waits for a POST /data payload from the Data-Collection system,
        then pauses at each phase so the user can inspect outputs and
        edit data/configs/user_input.json before continuing.

  [2] Testing (automated)
        Builds a synthetic payload internally — no network required.
        Simulates all user decisions automatically and runs the full
        pipeline end-to-end without stopping.
"""

import json
import os
import threading

from Data.preparedSession import PreparedSession
from Data.learningSet import LearningSet
from Data.hyperParameters import HyperParameters
from src.developmentSystemOrchestrator import (
    DevelopmentSystemOrchestrator,
    STATUS_FILE_PATH,
    DATA_FOLDER,
)
from src.communicationController import CommunicationController, LISTEN_PORT

RECEIVED_DATA      = "data/internal/received_data.json"
LEARNING_SETS_PATH = os.path.join(DATA_FOLDER, "internal/learning_sets.json")


# ── Mode selection ─────────────────────────────────────────────────────────

def ask_testing_mode() -> bool:
    """
    Prompt the user to choose a run mode.
    Returns True for testing mode, False for stop&go interactive mode.
    """
    print("\n" + "=" * 60)
    print("  Development System — Startup")
    print("=" * 60)
    print("  [1]  Stop & Go  (interactive, real network data)")
    print("  [2]  Testing    (automated, synthetic data)")
    print("=" * 60)

    while True:
        choice = input("  Select mode [1/2]: ").strip()
        if choice == "1":
            print("\n[Main] Mode selected: Stop & Go\n")
            return False
        elif choice == "2":
            print("\n[Main] Mode selected: Testing\n")
            return True
        else:
            print("  Invalid choice — please enter 1 or 2.")


# ── Payload parsers ────────────────────────────────────────────────────────

def parse_learning_set(payload: dict) -> LearningSet:
    """Build a LearningSet from the received JSON payload."""

    def parse_split(sessions: list) -> list:
        return [
            PreparedSession(
                UUID=s.get("UUID", ""),
                idPlayer=s.get("idPlayer", ""),
                skillOverall=float(s.get("skillOverall", 0.0)),
                socialInfluence=float(s.get("socialInfluence", 0.0)),
                injuriesImpact=float(s.get("injuriesImpact", 0.0)),
                label=int(s.get("label", 0)),
            )
            for s in sessions
        ]

    ls = payload["learning_set"]
    return LearningSet(
        training_set=parse_split(ls.get("training_set", [])),
        validation_set=parse_split(ls.get("validation_set", [])),
        test_set=parse_split(ls.get("test_set", [])),
    )


def parse_hyper_parameters(payload: dict) -> list:
    """Build a list of HyperParameters from the received JSON payload."""
    return [
        HyperParameters(
            classifier_id=hp.get("classifier_id", f"clf_{i}"),
            num_layers=int(hp.get("num_layers", 2)),
            num_neurons=int(hp.get("num_neurons", 64)),
            num_iterations=int(hp.get("num_iterations", 200)),
        )
        for i, hp in enumerate(payload.get("hyper_parameters", []))
    ]


def parse_config(payload: dict) -> dict:
    """Extract pipeline configuration thresholds from the payload."""
    cfg = payload.get("config", {})
    return {
        "overfitting_threshold":    float(cfg.get("overfitting_threshold",    0.3)),
        "generalization_threshold": float(cfg.get("generalization_threshold", 0.5)),
        "max_outer_iterations":     int(cfg.get("max_outer_iterations",       3)),
    }


# ── Synthetic payload for testing mode ────────────────────────────────────

def build_synthetic_payload() -> dict:
    """Generate a self-contained payload — no network required."""
    import uuid
    import numpy as np
    from sklearn.preprocessing import StandardScaler

    rng = np.random.default_rng(42)
    n   = 300

    skill    = rng.uniform(0, 1, n)
    social   = rng.uniform(0, 1, n)
    injuries = rng.uniform(0, 1, n)

    raw_score = 2.0 * skill - 1.5 * injuries + 0.8 * social + rng.normal(0, 0.3, n)
    labels    = np.clip(
        np.round(1 + 4 * (raw_score - raw_score.min()) / np.ptp(raw_score)),
        1, 5
    ).astype(int).tolist()

    X = StandardScaler().fit_transform(np.column_stack([skill, social, injuries]))

    def make_split(indices):
        return [
            {
                "UUID":            str(uuid.uuid4()),
                "idPlayer":        f"player_{i}",
                "skillOverall":    float(X[i, 0]),
                "socialInfluence": float(X[i, 1]),
                "injuriesImpact":  float(X[i, 2]),
                "label":           labels[i],
            }
            for i in indices
        ]

    return {
        "hyper_parameters": [
            {"classifier_id": "clf_A", "num_layers": 2, "num_neurons": 32,  "num_iterations": 200},
            {"classifier_id": "clf_B", "num_layers": 3, "num_neurons": 64,  "num_iterations": 300},
            {"classifier_id": "clf_C", "num_layers": 4, "num_neurons": 128, "num_iterations": 400},
        ],
        "learning_set": {
            "training_set":   make_split(range(0,   210)),
            "validation_set": make_split(range(210, 255)),
            "test_set":       make_split(range(255, 300)),
        },
        "config": {
            "overfitting_threshold":    0.3,
            "generalization_threshold": 0.5,
            "max_outer_iterations":     3,
        },
    }


# ── Pipeline launcher ──────────────────────────────────────────────────────

def launch_pipeline(payload: dict, testing_mode: bool) -> None:
    """Parse payload and hand off to the orchestrator."""
    orchestrator = DevelopmentSystemOrchestrator(
        learning_set=parse_learning_set(payload),
        hyper_param_configs=parse_hyper_parameters(payload),
        testing_mode=testing_mode,
        **parse_config(payload),
    )
    orchestrator.run()


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":

    testing_mode = ask_testing_mode()

    if testing_mode:
        # ── Testing: synthetic data, no network, fully automated ───────
        print("[Main] Building synthetic payload …")
        launch_pipeline(build_synthetic_payload(), testing_mode=True)

    else:
        # ── Stop & Go: check whether we are resuming or starting fresh ─
        resuming = (
            os.path.isfile(STATUS_FILE_PATH)
            and json.load(open(STATUS_FILE_PATH, encoding="UTF-8"))
                    .get("phase", "Starting") not in ("Starting",)
        )

        if resuming:
            # Resume from the last persisted phase — no network needed
            print("[Main] Resuming pipeline from persisted phase …")
            with open(LEARNING_SETS_PATH, "r", encoding="UTF-8") as f:
                payload = json.load(f)
            launch_pipeline(payload, testing_mode=False)

        else:
            # Fresh start: spin up REST server and wait for the payload
            print("[Main] Waiting for learning-set payload via POST /data …")
            print(f"[Main] Listening on port {LISTEN_PORT} …\n")

            received_event   = threading.Event()
            received_payload: dict = {}

            def handle_message(payload: dict) -> None:
                """Save payload to disk, then unblock the main thread."""
                os.makedirs(os.path.dirname(LEARNING_SETS_PATH), exist_ok=True)
                with open(LEARNING_SETS_PATH, "w", encoding="UTF-8") as f:
                    json.dump(payload, f, indent="\t")
                received_payload.update(payload)
                received_event.set()

            comm = CommunicationController(received_data_path=RECEIVED_DATA)
            comm.start_server(handle_message)

            received_event.wait()   # block until POST /data arrives
            print("[Main] Payload received — starting pipeline.\n")
            launch_pipeline(received_payload, testing_mode=False)