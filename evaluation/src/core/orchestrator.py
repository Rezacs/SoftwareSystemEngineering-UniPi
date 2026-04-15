"""Main orchestration logic for the evaluation workflow."""
import json
import threading
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

from src.reporting.report_metrics import ReportMetrics
from src.reporting.visual_report import VisualReport
from src.utils.logger import logger
from src.core.logging_manager import LoggingManager

# ── Global matplotlib lock (shared across all instances) ──────
_matplotlib_lock = threading.Lock()


class Orchestrator:
    """
    Main controller of Evaluation System (continuous streaming version)
    """

    def __init__(self, repo, batch_mgr, config, state):
        self.repo      = repo
        self.batch_mgr = batch_mgr
        self.config    = config
        self.state     = state

        # ================= CONFIG =================
        self.eval_cfg     = config["evaluation"]
        self.paths_cfg    = config["paths"]
        self.external_cfg = config["external_systems"]

        # ================= COMPONENTS =================
        self.metrics_engine = ReportMetrics()
        self.visual         = VisualReport()
        self.log_mgr        = LoggingManager()

        # ================= INTERNAL STATE =================
        self.last_metrics   = None
        self.last_batch     = None
        self._finalize_lock = threading.Lock()
        self._finalized     = False  # guard against double-finalize

    # =========================================================
    # ================= VISUAL (fire-and-forget) ==============
    # =========================================================

    def _generate_visual_async(self, batch):
        """
        Spawn a background thread to generate the plot.
        The HTTP response is never blocked waiting for this.
        """
        def _run():
            try:
                with _matplotlib_lock:
                    result = self.visual.generate(batch, self.config)
                logger.info(f"Report generated → {result.get('file')}")
            except Exception as e:
                logger.error(f"Visual generation failed: {e}")

        threading.Thread(target=_run, daemon=True).start()

    # =========================================================
    # ================= MAIN ENTRY ============================
    # =========================================================

    def process(self, data):
        """Process incoming label data and manage batch evaluation flow."""
        # ================= START SESSION + E1 =================
        self.log_mgr.start_session()
        self.log_mgr.start_process("E1")

        # ================= WAITING DECISION CHECK =================
        if self.state.is_waiting_decision():

            if self.config["server"]["mode"] == "auto":

                with self._finalize_lock:
                    # re-check inside the lock (double-checked locking)
                    if not self.state.is_waiting_decision():
                        pass
                    elif self._finalized:
                        # another thread already claimed finalization → buffer
                        self.repo.save_label(data)
                        return {"status": "buffering_until_decision"}
                    else:
                        self._finalized = True  # claim finalization
                        decision = self._suggest_decision(self.last_metrics)

                        # END E1 (waiting path)
                        self.log_mgr.end_process("Label Sufficient: NO")

                        return self.finalize_decision(decision, mode="AUTO")

                # fell through — state was already cleared by winning thread
                self.repo.save_label(data)
                return {"status": "buffering_until_decision"}

            else:
                logger.info("⏸ Waiting for human decision → buffering incoming data")
                self.repo.save_label(data)

                # END E1
                self.log_mgr.end_process("Label Sufficient: NO")

                self.log_mgr.finalize_log()
                return {"status": "buffering_until_decision"}

        # ================= RECEIVE =================
        logger.info(
            f"Received {data['source']} label → "
            f"player_id: {data['player_id']} has label: {data['label']}"
        )

        # ================= STORE =================
        self.repo.save_label(data)

        # ================= FETCH MATCHED =================
        pairs = self.repo.get_matched_pairs()

        logger.info(
            f"Available: {len(pairs)} | Using: {min(len(pairs), self.eval_cfg['batch_size'])}"
        )

        # ================= CHECK BATCH =================
        if not self.batch_mgr.is_ready(pairs):
            logger.info("Waiting for more matched pairs...")

            # END E1 (NOT sufficient)
            self.log_mgr.end_process("Label Sufficient: NO")

            self.log_mgr.finalize_log()
            return {"status": "waiting_for_data"}

        # ================= BATCH READY =================
        logger.info("Batch ready → Evaluating...")

        # END E1 (YES)
        self.log_mgr.end_process("Label Sufficient: YES")

        # ================= BUILD BATCH =================
        batch = self.batch_mgr.get_batch(pairs)

        # ================= METRICS =================
        batch_metrics = self.metrics_engine.compute(
            batch,
            self.eval_cfg["error_threshold"]
        )

        # ================= REPORT (non-blocking) =================
        # Response is returned immediately — plot is written in the background
        self._generate_visual_async(batch)

        # ================= SAVE =================
        self.last_metrics = batch_metrics
        self.last_batch   = batch

        self._save_json("matched_pairs.json", batch)
        self._save_json("metrics.json", batch_metrics)

        # ================= MARK WAITING =================
        self.state.set_batch(batch)

        # ================= CLEAR USED DATA =================
        if self.eval_cfg.get("reset_after_batch", True):
            self.repo.delete_used(batch)
            logger.info("Buffer Cleared → Only consumed batch removed from DB")

        # ================= DECISION SUGGESTION =================
        decision = self._suggest_decision(batch_metrics)

        # ================= AUTO MODE =================
        if self.config["server"]["mode"] == "auto":
            with self._finalize_lock:
                if self._finalized:
                    return {"status": "already_finalized", "decision": decision}
                self._finalized = True
                return self.finalize_decision(decision, mode="AUTO")

        # ================= HUMAN MODE =================
        logger.info("⏸ Waiting for HUMAN decision")
        return {
            "status":             "waiting_for_human",
            "metrics":            batch_metrics,
            "suggested_decision": decision
        }

    # =========================================================
    # ================= FINAL DECISION ========================
    # =========================================================

    def finalize_decision(self, decision, mode="HUMAN"):
        """Finalize the batch decision and reset the system state."""
        logger.info(f"{mode} DECISION → {decision}")

        # ================= START E2 =================
        self.log_mgr.start_process("E2")

        output = {
            "decision": decision,
            "metrics":  self.last_metrics
        }

        # ================= HANDLE REJECT =================
        if decision == "REJECT":
            output["action"] = "SEND_TO_MESSAGING"
            self._simulate_messaging(output)

            self.log_mgr.end_process("Classifier Good: NO")

        else:
            self.log_mgr.end_process("Classifier Good: YES")

        # ================= FINALIZE LOG =================
        self.log_mgr.finalize_log()

        # ================= SAVE OUTPUT =================
        self._save_json("decision.json", output)

        # ================= RESET STATE =================
        self.state.clear_batch()
        self._finalized = False  # re-arm for next batch

        logger.info("🔄 System ready for next batch\n" + "=" * 62 + "\n")

        return output

    # =========================================================
    # ================= DECISION LOGIC ========================
    # =========================================================

    def _suggest_decision(self, batch_metrics):

        if batch_metrics["errors"] > self.eval_cfg["max_errors"]:
            return "REJECT"

        if batch_metrics["max_consecutive"] > self.eval_cfg["max_consecutive_errors"]:
            return "REJECT"

        return "ACCEPT"

    # =========================================================
    # ================= MESSAGING =============================
    # =========================================================

    def _simulate_messaging(self, payload):

        if not self.external_cfg["messaging"]["enabled"]:
            logger.info("Messaging disabled (simulation only)")
            return

        logger.warning("Sending REJECT classifier config to messaging system (SIMULATED)")
        logger.info(json.dumps(payload, indent=2))

    # =========================================================
    # ================= UTIL ==================================
    # =========================================================

    def _save_json(self, filename, data):

        output_dir = Path(self.paths_cfg["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        path = output_dir / filename

        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)