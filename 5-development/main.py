"""
Entry point for the Development System.

Stop&Go mode  (testing_mode=False):
    The app starts a REST server, waits for a POST /data payload from
    another machine, parses it into domain objects, then runs the
    state-machine pipeline. Each phase ends with sys.exit(0); re-running
    main.py resumes from the persisted phase automatically.

Testing mode  (testing_mode=True):
    Payload is generated synthetically — no network required.
    The pipeline runs end-to-end without stopping.
"""

import threading

from Data.preparedSession import PreparedSession
from Data.learningSet import LearningSet
from Data.hyperParameters import HyperParameters
from src.developmentSystemOrchestrator import DevelopmentSystemOrchestrator
from src.communicationController import CommunicationController

# ── Configuration ──────────────────────────────────────────────────────────
TESTING_MODE  = True   # set True for fully automated end-to-end testing
LISTEN_PORT   = 5000
RECEIVED_DATA = "data/internal/received_data.json"


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
        "overfitting_threshold":    float(cfg.get("overfitting_threshold",    0.1)),
        "generalization_threshold": float(cfg.get("generalization_threshold", 0.15)),
        "max_outer_iterations":     int(cfg.get("max_outer_iterations",       3)),
    }


# ── Synthetic payload for testing mode ────────────────────────────────────

def build_synthetic_payload() -> dict:
    import uuid
    import numpy as np
    from sklearn.preprocessing import StandardScaler

    rng = np.random.default_rng(42)
    n   = 300

    skill    = rng.uniform(0, 1, n)
    social   = rng.uniform(0, 1, n)
    injuries = rng.uniform(0, 1, n)

    # Score is a noisy function of the three features, mapped to 1–5
    raw_score = 2.0 * skill - 1.5 * injuries + 0.8 * social + rng.normal(0, 0.3, n)
    labels    = np.clip(np.round(
        1 + 4 * (raw_score - raw_score.min()) / (raw_score.ptp())
    ), 1, 5).astype(int).tolist()

    X = np.column_stack([skill, social, injuries])
    X = StandardScaler().fit_transform(X)

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
            "overfitting_threshold":    0.3,   # MAE units now, not accuracy
            "generalization_threshold": 0.5,
            "max_outer_iterations":     3,
        },
    }


# ── Entry point ────────────────────────────────────────────────────────────

def launch_pipeline(payload: dict) -> None:
    """Parse payload and hand off to the orchestrator."""
    learning_set  = parse_learning_set(payload)
    hp_configs    = parse_hyper_parameters(payload)
    config        = parse_config(payload)

    orchestrator = DevelopmentSystemOrchestrator(
        learning_set=learning_set,
        hyper_param_configs=hp_configs,
        testing_mode=TESTING_MODE,
        **config,
    )
    orchestrator.run()


if __name__ == "__main__":

    if TESTING_MODE:
        # ── Testing: no network, synthetic data, runs end-to-end ──────
        print("[Main] Testing mode — using synthetic payload.")
        launch_pipeline(build_synthetic_payload())

    else:
        # ── Interactive stop&go ───────────────────────────────────────
        import json, os
        from src.developmentSystemOrchestrator import (
            STATUS_FILE_PATH, DATA_FOLDER
        )

        # Check if we are resuming a stopped pipeline
        resuming = (
            os.path.isfile(STATUS_FILE_PATH)
            and json.load(open(STATUS_FILE_PATH)).get("phase", "Starting") != "Starting"
        )

        if resuming:
            # ── Resume: reload the persisted learning set and continue ─
            print("[Main] Resuming pipeline from persisted phase …")
            LEARNING_SETS_PATH = os.path.join(DATA_FOLDER, "internal/learning_sets.json")

            with open(LEARNING_SETS_PATH, "r", encoding="UTF-8") as f:
                payload = json.load(f)

            launch_pipeline(payload)

        else:
            # ── Fresh start: wait for payload via REST ─────────────────
            print("[Main] Waiting for data payload via POST /data …")

            received_event = threading.Event()
            received_payload: dict = {}

            def handle_message(payload: dict) -> None:
                # Persist the raw payload so future restarts can reload it
                os.makedirs(os.path.join(DATA_FOLDER, "internal"), exist_ok=True)
                with open(
                    os.path.join(DATA_FOLDER, "internal/learning_sets.json"),
                    "w", encoding="UTF-8"
                ) as f:
                    json.dump(payload, f, indent="\t")

                received_payload.update(payload)
                received_event.set()    # unblock the main thread

            comm = CommunicationController(
                port=LISTEN_PORT,
                received_data_path=RECEIVED_DATA,
            )
            comm.start_server(handle_message)

            # Block until a payload arrives
            received_event.wait()
            print("[Main] Payload received — starting pipeline.")
            launch_pipeline(received_payload)