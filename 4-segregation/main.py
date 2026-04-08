"""
Entry point for the Segregation System.
Runs the orchestrator with mode selection (Stop&Go or Testing).
"""

import json
import os
import threading
import time

from src.orchestrator import SegregationSystemOrchestrator
from src.communication_controller import CommunicationController


# ── Config path ────────────────────────────────────────────────────────────
CONFIG_PATH = os.path.join("..", "config", "segregationConfig.json")


def _read_config() -> dict:
    """Load configuration from config.json."""
    if not os.path.isfile(CONFIG_PATH):
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="UTF-8") as f:
        return json.load(f)


# ── Mode selection ─────────────────────────────────────────────────────────

def ask_testing_mode() -> bool:
    """Prompt the user to choose a run mode. Returns True for testing mode."""
    print("\n" + "=" * 60)
    print("  Segregation System — Startup")
    print("=" * 60)
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


if __name__ == "__main__":
    # Ask mode only once at startup
    testing_mode = ask_testing_mode()
    cfg = _read_config()
    
    workflow_state_path = os.path.join("data", "output", "segregation_workflow_state.json")
    
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
    # In Stop&Go mode, it processes one step at a time (exits after each checkpoint).
    # In Testing mode, it runs continuously until interrupted.
    
    while True:
        try:
            result = launch_pipeline(testing_mode)
            status = result.get("status", "unknown")
            
            if status == "sessions_not_sufficient":
                # Not enough sessions yet, wait a bit
                if testing_mode:
                    print("[Main] Not enough sessions yet, checking again in 5 seconds...")
                    time.sleep(5)
                else:
                    print("[Main] Not enough sessions. Waiting for more data...")
                    print("[Main] The system will check again when you run it next time.")
                    break  # In Stop&Go, we exit and wait for user to restart
            
            elif status == "balancing_report_generated":
                # Balancing report created, now waiting for decision
                print(f"\n[Main] Status: Balancing report generated")
                if testing_mode:
                    # In testing mode, continue automatically (decision will be simulated)
                    print("[Main] Continuing to decision phase...")
                    time.sleep(1)
                else:
                    # In Stop&Go mode, exit and wait for user decision
                    print(f"[Main] Please review the report and provide your decision.")
                    print(f"  → Report: {result.get('report_path')}")
                    print(f"  → Plot: {result.get('plot_path')}")
                    print(f"  → Decision file: {result.get('decision_path')}")
                    print(f"\n[Main] After updating the decision file, run 'python main.py' again.")
                    break
            
            elif status == "coverage_report_generated":
                # Coverage report created, now waiting for decision
                print(f"\n[Main] Status: Coverage report generated")
                if testing_mode:
                    # In testing mode, continue automatically (decision will be simulated)
                    print("[Main] Continuing to decision phase...")
                    time.sleep(1)
                else:
                    # In Stop&Go mode, exit and wait for user decision
                    print(f"[Main] Please review the report and provide your decision.")
                    print(f"  → Report: {result.get('report_path')}")
                    print(f"  → Plot: {result.get('plot_path')}")
                    print(f"  → Decision file: {result.get('decision_path')}")
                    print(f"\n[Main] After updating the decision file, run 'python main.py' again.")
                    break
                    
            elif status in ["waiting_balancing_decision", "waiting_coverage_decision"]:
                # Waiting for decision (should only happen in Stop&Go after restart)
                print(f"\n[Main] Status: {status.replace('_', ' ')}")
                if testing_mode:
                    # In testing mode, decisions are simulated automatically
                    print("[Main] Simulating decision...")
                    time.sleep(1)
                else:
                    # In Stop&Go mode, decision file not found yet
                    print(f"[Main] Waiting for decision file: {result.get('decision_path')}")
                    print(f"[Main] Run again after providing your decision.")
                    break
                    
            elif status == "balancing_rejected" or status == "coverage_rejected":
                # Workflow rejected, reset complete
                print(f"\n[Main] Status: {status.replace('_', ' ')}")
                if testing_mode:
                    print("[Main] System reset. Checking for new sessions...")
                    time.sleep(2)
                else:
                    print("[Main] System reset. Run again when ready to process new sessions.")
                    break
                    
            elif status == "calibration_sets_sent":
                # Workflow complete!
                print("\n[Main] Status: Calibration set sent successfully!")
                if testing_mode:
                    print("[Main] System reset. Ready for next batch...")
                    time.sleep(5)  # Wait before next cycle in testing mode
                else:
                    print("[Main] Returning to idle. Run again to process new sessions.")
                    break
                    
            elif status == "reset_complete":
                # Already completed, was reset
                print("[Main] Status: System is idle")
                print("[Main] Checking for sessions...")
                time.sleep(5)
                
            else:
                # Any other status - just log and continue/exit based on mode
                print(f"[Main] Status: {status}")
                if testing_mode:
                    time.sleep(2)
                else:
                    break
                    
        except KeyboardInterrupt:
            print("\n[Main] Shutdown requested by user.")
            break
        except Exception as e:
            print(f"[Main] Error during execution: {e}")
            if testing_mode:
                print("[Main] Waiting 10 seconds before retry...")
                time.sleep(10)
            else:
                break
