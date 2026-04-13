"""
Entry point for the Segregation System.
Runs the orchestrator with mode selection (Stop&Go or Testing).
"""

import json
import threading
import time
from pathlib import Path
from typing import Optional

from src.orchestrator import SegregationSystemOrchestrator
from src.communication_controller import CommunicationController


# ── Config path ────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "segregationConfig.json"


def _read_config() -> dict:
    """Load configuration from config.json."""
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")
    with CONFIG_PATH.open("r", encoding="UTF-8") as f:
        return json.load(f)


# ── Mode selection ─────────────────────────────────────────────────────────

def ask_testing_mode() -> bool:
    """Prompt the user to choose a run mode. Returns True for testing mode."""
    print("  [1]  Stop & Go  (interactive — manual decision files)")
    print("  [2]  Testing    (automated  — decisions simulated 70/30)")
    print("  Both modes process incoming sessions automatically.")
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


# ── Main execution ─────────────────────────────────────────────────────────

def launch_pipeline(testing_mode: bool) -> dict:
    """Execute the segregation orchestrator."""
    orchestrator = SegregationSystemOrchestrator(testing_mode=testing_mode)
    result = orchestrator.run()
    
    # If calibration set was sent, also send it to downstream system
    if result.get("status") == "calibration_sets_sent":
        calibration_set = result.get("calibration_set")
        comm = CommunicationController()
        sent, details = comm.send_calibration_set(calibration_set)
        result["calibration_set_delivery"] = {
            "sent": sent,
            "details": details,
        }
        print(f"[Main] Calibration set delivery: {'SUCCESS' if sent else 'FAILED'}")
        if not sent:
            print(f"  → Details: {details}")
    
    return result


def wait_for_decision_confirmation(decision_path: Optional[str]):
    """Block until user confirms decision file update in Stop&Go mode."""
    if decision_path:
        print(f"[Main] Decision file to update: {decision_path}")
    while True:
        user_input = input("[Main] Press Enter when decision file is updated (q to quit): ").strip().lower()
        if user_input == "":
            return
        if user_input in {"q", "quit", "exit"}:
            raise KeyboardInterrupt
        print("[Main] Invalid input. Press Enter to continue or 'q' to quit.")


if __name__ == "__main__":
    # Ask mode only once at startup
    testing_mode = ask_testing_mode()
    cfg = _read_config()
    
    workflow_state_path = REPO_ROOT / "data" / "output" / "segregation_workflow_state.json"
    
    # ── Start persistent background server ─────────────────────────────────
    print("[Main] Starting REST API server in background...")
    comm = CommunicationController()
    
    def start_server():
        comm.start_server()
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(2)  # Give the server time to start
    
    print(f"[Main] REST API listening on {cfg['segregationSystemIpAddress']}:{cfg['segregationSystemPort']}")
    print(f"[Main] Segregation System started in {'Testing' if testing_mode else 'Stop & Go'} mode")
    print(f"[Main] Waiting for sessions to accumulate...\n")
    
    # ── THE CONTINUOUS LOOP ────────────────────────────────────────────────
    # The system processes sessions continuously with the selected mode.
    # In both modes, it runs continuously until interrupted (Ctrl+C).
    
    insufficient_sessions_logged = False
    waiting_for_input_logged = False

    while True:
        try:
            result = launch_pipeline(testing_mode)
            status = result.get("status", "unknown")
            
            if status == "sessions_not_sufficient":
                waiting_for_input_logged = False
                # Not enough sessions yet, wait a bit
                if testing_mode:
                    if not insufficient_sessions_logged:
                        print("[Main] Not enough sessions yet. Waiting for incoming sessions...")
                        insufficient_sessions_logged = True
                    time.sleep(5)
                else:
                    if not insufficient_sessions_logged:
                        print("[Main] Not enough sessions. Waiting for more data...")
                        insufficient_sessions_logged = True
                    time.sleep(5)

            elif status == "waiting_for_input":
                insufficient_sessions_logged = False
                if not waiting_for_input_logged:
                    print("[Main] Waiting for a new incoming session...")
                    waiting_for_input_logged = True
                time.sleep(5)
            
            elif status == "balancing_report_generated":
                insufficient_sessions_logged = False
                waiting_for_input_logged = False
                # Balancing report created, now waiting for decision
                print(f"\n[Main] Status: Balancing report generated")
                if testing_mode:
                    # In testing mode, continue automatically (decision will be simulated)
                    print("[Main] Continuing to decision phase...")
                    time.sleep(1)
                else:
                    # In Stop&Go mode, keep running and wait for user decision
                    print(f"[Main] Please review the report and provide your decision.")
                    print(f"  → Report: {result.get('report_path')}")
                    print(f"  → Plot: {result.get('plot_path')}")
                    print(f"  → Decision file: {result.get('decision_path')}")
                    wait_for_decision_confirmation(result.get("decision_path"))
            
            elif status == "coverage_report_generated":
                insufficient_sessions_logged = False
                waiting_for_input_logged = False
                # Coverage report created, now waiting for decision
                print(f"\n[Main] Status: Coverage report generated")
                if testing_mode:
                    # In testing mode, continue automatically (decision will be simulated)
                    print("[Main] Continuing to decision phase...")
                    time.sleep(1)
                else:
                    # In Stop&Go mode, keep running and wait for user decision
                    print(f"[Main] Please review the report and provide your decision.")
                    print(f"  → Report: {result.get('report_path')}")
                    print(f"  → Plot: {result.get('plot_path')}")
                    print(f"  → Decision file: {result.get('decision_path')}")
                    wait_for_decision_confirmation(result.get("decision_path"))
                    
            elif status in ["waiting_balancing_decision", "waiting_coverage_decision"]:
                insufficient_sessions_logged = False
                waiting_for_input_logged = False
                # Waiting for decision (should only happen in Stop&Go after restart)
                print(f"\n[Main] Status: {status.replace('_', ' ')}")
                if testing_mode:
                    # In testing mode, decisions are simulated automatically
                    print("[Main] Simulating decision...")
                    time.sleep(1)
                else:
                    # In Stop&Go mode, decision file not found yet
                    print(f"[Main] Waiting for decision file: {result.get('decision_path')}")
                    wait_for_decision_confirmation(result.get("decision_path"))
                    
            elif status == "balancing_rejected" or status == "coverage_rejected":
                insufficient_sessions_logged = False
                waiting_for_input_logged = False
                # Workflow rejected, reset complete
                print(f"\n[Main] Status: {status.replace('_', ' ')}")
                if testing_mode:
                    print("[Main] System reset. Checking for new sessions...")
                    time.sleep(2)
                else:
                    print("[Main] System reset. Waiting for new sessions...")
                    time.sleep(2)
                    
            elif status == "calibration_sets_sent":
                insufficient_sessions_logged = False
                waiting_for_input_logged = False
                # Workflow complete!
                print("\n[Main] Status: Calibration set sent successfully!")
                if testing_mode:
                    print("[Main] System reset. Ready for next batch...")
                    time.sleep(5)  # Wait before next cycle in testing mode
                else:
                    print("[Main] Returning to idle. Waiting for next sessions...")
                    time.sleep(2)
                    
            elif status == "reset_complete":
                insufficient_sessions_logged = False
                waiting_for_input_logged = False
                # Already completed, was reset
                print("[Main] Status: System is idle")
                print("[Main] Checking for sessions...")
                time.sleep(5)
                
            else:
                insufficient_sessions_logged = False
                waiting_for_input_logged = False
                # Any other status - just log and continue/exit based on mode
                print(f"[Main] Status: {status}")
                time.sleep(2)
                    
        except KeyboardInterrupt:
            print("\n[Main] Shutdown requested by user.")
            break
        except Exception as e:
            print(f"[Main] Error during execution: {e}")
            print("[Main] Waiting 10 seconds before retry...")
            time.sleep(10)
