"""
Entry point for the Development System.
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
                UUID=s.get("session_id", ""),
                idPlayer=str(s.get("player_id", "")),
                skillOverall=float(s.get("skill_overall", 0.0)),
                socialInfluence=float(s.get("social_influence_score", 0.0)),
                injuriesImpact=float(s.get("injuries_impact_score", 0.0)),
                label=int(s.get("label", 0)),
            )
            for s in sessions
        ]
    return LearningSet(
        training_set=parse_split(payload.get("training_set", [])),
        validation_set=parse_split(payload.get("validation_set", [])),
        test_set=parse_split(payload.get("test_set", [])),
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
        testing_mode=testing_mode,
    )
    orchestrator.run()

if __name__ == "__main__":
    testing_mode = ask_testing_mode()
    cfg = _read_config()

    status_path = cfg["paths"]["status_file"]
    learning_sets_path = cfg["paths"]["learning_sets"]
    received_data_path = cfg["paths"]["received_data"]
    listen_port = int(cfg["network"]["listen_port"])

    # ── Setup Persistence Events ───────────────────────────────────────────
    received_event = threading.Event()
    received_payload: dict = {}

    def handle_message(payload: dict) -> None:
        try:
            parse_learning_set(payload)  # only this remains for validation

            os.makedirs(os.path.dirname(learning_sets_path), exist_ok=True)
            with open(learning_sets_path, "w", encoding="UTF-8") as f:
                json.dump(payload, f, indent="\t")

            received_payload.clear()
            received_payload.update(payload)
            received_event.set()
            print("\n[Main] Valid payload received. Unblocking pipeline...")
        except Exception as e:
            print(f"[Main] Logic Validation Error: {e}")

    # ── Start persistent background server ─────────────────────────────────
    comm = CommunicationController(
        listen_host=cfg["network"]["listen_host"],
        listen_port=listen_port,
        segregation_ip=cfg["network"]["segregation_system"]["ip"],
        segregation_port=int(cfg["network"]["segregation_system"]["port"]),
        production_ip=cfg["network"]["production_system"]["ip"],
        production_port=int(cfg["network"]["production_system"]["port"]),
        production_endpoint=cfg["network"]["production_system"]["endpoint"],
        received_data_path=received_data_path,
        rejected_report_path=cfg["paths"]["rejected_report"],
    )
    comm.start_server(handle_message)

    # ── THE CONTINUOUS LOOP ────────────────────────────────────────────────
    while True:
        # Check if we are resuming a saved state
        resuming = (
            os.path.isfile(status_path)
            and json.load(open(status_path, encoding="UTF-8")).get("phase", "Starting") != "Starting"
        )

        if resuming:
            print("[Main] RESUMING: Found existing status. Loading persisted learning set...")
            with open(learning_sets_path, "r", encoding="UTF-8") as f:
                current_payload = json.load(f)
        else:
            print(f"\n[Main] IDLE: Waiting for new payload on port {listen_port}...")
            received_event.wait() # Pause main thread until handle_message sets event
            current_payload = received_payload.copy()
            received_event.clear() # Reset for the next message arrival

        # Execute Pipeline
        try:
            launch_pipeline(current_payload, testing_mode)
            print("\n[Main] Pipeline cycle finished. Returning to listening state.")
        except Exception as e:
            print(f"[Main] Error during execution: {e}")
            # If a crash happens, we reset the status file to avoid an infinite crash-loop
            if os.path.exists(status_path): os.remove(status_path)