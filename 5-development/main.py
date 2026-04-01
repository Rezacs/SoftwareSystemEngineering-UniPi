"""
Entry point for the Development System.

On startup the user is asked which mode to run:

  [1] Stop&Go (interactive)
        Waits for a POST /data payload, then pauses at each phase
        so the user can inspect outputs and edit user_input.json.

  [2] Testing (automated)
        Also waits for a real POST /data payload (no synthetic data).
        User decisions are simulated automatically from report files.
        The pipeline runs end-to-end without stopping.

All configuration is loaded from Data/configs/config.json by the
DevelopmentSystemOrchestrator — main.py only handles startup logic.
"""

import json
import os
import threading

from Data.preparedSession import PreparedSession
from Data.learningSet import LearningSet
from Data.hyperParameters import HyperParameters
from src.developmentSystemOrchestrator import DevelopmentSystemOrchestrator
from src.communicationController import CommunicationController

# ── Config is loaded here only to know the listen port and file paths ──────
_CONFIG_PATH = os.path.join("Data", "configs", "config.json")

def _read_config() -> dict:
    with open(_CONFIG_PATH, "r", encoding="UTF-8") as f:
        return json.load(f)


# ── Mode selection ─────────────────────────────────────────────────────────

def ask_testing_mode() -> bool:
    """Prompt the user to choose a run mode. Returns True for testing mode."""
    print("\n" + "=" * 60)
    print("  Development System — Startup")
    print("=" * 60)
    print("  [1]  Stop & Go  (interactive — human edits user_input.json)")
    print("  [2]  Testing    (automated  — decisions simulated from reports)")
    print("  Both modes wait for a real HTTP POST /data payload.")
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
    return [
        HyperParameters(
            classifier_id=hp.get("classifier_id", f"clf_{i}"),
            num_layers=int(hp.get("num_layers", 2)),
            num_neurons=int(hp.get("num_neurons", 64)),
            num_iterations=int(hp.get("num_iterations", 200)),
        )
        for i, hp in enumerate(payload.get("hyper_parameters", []))
    ]


# ── Pipeline launcher ──────────────────────────────────────────────────────

def launch_pipeline(payload: dict, testing_mode: bool) -> None:
    orchestrator = DevelopmentSystemOrchestrator(
        learning_set=parse_learning_set(payload),
        hyper_param_configs=parse_hyper_parameters(payload),
        testing_mode=testing_mode,
    )
    orchestrator.run()


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    testing_mode = ask_testing_mode()
    cfg          = _read_config()

    status_path      = cfg["paths"]["status_file"]
    learning_sets_path = cfg["paths"]["learning_sets"]
    received_data_path = cfg["paths"]["received_data"]
    listen_port      = int(cfg["network"]["listen_port"])

    # ── Check whether we are resuming a stopped pipeline ──────────────
    resuming = (
        os.path.isfile(status_path)
        and json.load(open(status_path, encoding="UTF-8"))
                .get("phase", "Starting") != "Starting"
    )

    if resuming:
        # Resume: reload the persisted learning set — no network needed
        print("[Main] Resuming pipeline from persisted phase …")
        with open(learning_sets_path, "r", encoding="UTF-8") as f:
            payload = json.load(f)
        launch_pipeline(payload, testing_mode)

    else:
        # Fresh start: wait for a real POST /data payload
        print(f"[Main] Waiting for learning-set payload via POST /data …")
        print(f"[Main] Listening on port {listen_port} …\n")

        received_event   = threading.Event()
        received_payload: dict = {}

       # -- Inside the main block of main.py --

        def handle_message(payload: dict) -> None:
            """
            Deep validation and persistence. 
            Triggered only if CommunicationController passed structural checks.
            """
            try:
                # 1. Attempt to parse - this validates data types and logic
                # parse_learning_set and parse_hyper_parameters are your existing functions
                parse_learning_set(payload)
                parse_hyper_parameters(payload)

                # 2. If parsing succeeded, persist as the "Clean/Valid" version
                os.makedirs(os.path.dirname(learning_sets_path), exist_ok=True)
                with open(learning_sets_path, "w", encoding="UTF-8") as f:
                    json.dump(payload, f, indent="\t")

                # 3. Update memory and unblock the pipeline
                received_payload.update(payload)
                received_event.set()
                print("[Main] Payload deeply validated and persisted to learning_sets.json")

            except Exception as e:
                # This catches things like 'NoneType' errors or missing sub-keys
                # within the sessions (e.g., a session missing 'skillOverall')
                print(f"[Main] Logic Validation Error: {e}")
                print("[Main] Pipeline will continue waiting for a VALID payload.")

        # Spin up a temporary Flask server just to receive the payload.
        # The orchestrator's CommunicationController will use its own
        # server instance for the rest of the pipeline if needed.
        comm = CommunicationController(
            listen_host         = cfg["network"]["listen_host"],
            listen_port         = listen_port,
            segregation_ip      = cfg["network"]["segregation_system"]["ip"],
            segregation_port    = int(cfg["network"]["segregation_system"]["port"]),
            production_ip       = cfg["network"]["production_system"]["ip"],
            production_port     = int(cfg["network"]["production_system"]["port"]),
            production_endpoint = cfg["network"]["production_system"]["endpoint"],
            received_data_path  = received_data_path,
            rejected_report_path= cfg["paths"]["rejected_report"],
        )
        comm.start_server(handle_message)

        received_event.wait()   # block until POST /data arrives
        print("[Main] Payload received — starting pipeline.\n")
        launch_pipeline(received_payload, testing_mode)