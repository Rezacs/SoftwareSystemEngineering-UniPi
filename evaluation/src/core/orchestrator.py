from sklearn import metrics

from src.reporting.report_metrics import ReportMetrics
from src.reporting.visual_report import VisualReport
from src.utils.logger import logger
import json
import os


class Orchestrator:
    """
    Main controller of Evaluation System (continuous streaming version)
    """

    def __init__(self, repo, batch_mgr, config, state):
        self.repo = repo
        self.batch_mgr = batch_mgr
        self.config = config
        self.state = state

        # ================= CONFIG =================
        self.eval_cfg = config["evaluation"]
        self.paths_cfg = config["paths"]
        self.external_cfg = config["external_systems"]

        # ================= COMPONENTS =================
        self.metrics_engine = ReportMetrics()
        self.visual = VisualReport()

        # ================= INTERNAL STATE =================
        self.last_metrics = None
        self.last_batch = None

    # =========================================================
    # ================= MAIN ENTRY =============================
    # =========================================================

    def process(self, data):

        # ================= WAITING DECISION CHECK =================
        if self.state.is_waiting_decision():
            logger.info("⏸ Waiting for human decision → buffering incoming data")
            self.repo.save_label(data)
            return {"status": "buffering_until_decision"}

        # ================= RECEIVE =================
        logger.info(
            f"Received {data['source']} label → player_id: {data['player_id']} has label: {data['label']}"
        )

        # ================= STORE =================
        self.repo.save_label(data)

        # ================= FETCH MATCHED =================
        pairs = self.repo.get_matched_pairs()

        #logger.info(f"Matched pairs: {len(pairs)} / {self.eval_cfg['batch_size']}")
        
        logger.info(f"Available: {len(pairs)} | Using: {min(len(pairs), self.eval_cfg['batch_size'])}"
)

        # ================= CHECK BATCH =================
        if not self.batch_mgr.is_ready(pairs):
            logger.info("Waiting for more matched pairs...")
            return {"status": "waiting_for_data"}

        # ================= BUILD BATCH =================
        batch = self.batch_mgr.get_batch(pairs)

        logger.info("Batch ready → Evaluating...")

        # ================= METRICS =================
        metrics = self.metrics_engine.compute(
            batch,
            self.eval_cfg["error_threshold"]
        )

        # ================= REPORT =================
        visual = self.visual.generate(batch, self.config)

        logger.info(f"Report generated → {visual.get('file')}")

        # ================= SAVE =================
        self.last_metrics = metrics
        self.last_batch = batch

        self._save_json("matched_pairs.json", batch)
        self._save_json("metrics.json", metrics)

        # ================= MARK WAITING =================
        self.state.set_batch(batch)

        
        if self.eval_cfg.get("reset_after_batch", True):
            self.repo.delete_used(batch)
            logger.info("Buffer Cleared → Only consumed batch removed from DB")

        decision = self._suggest_decision(metrics)
         #====== AUTO MODE ===========
        if self.config["server"]["mode"] == "auto":
            return self.finalize_decision(decision, mode="AUTO")

        # ======== HUMAN MODE =================
        logger.info("⏸ Waiting for HUMAN decision")

        return {
            "status": "waiting_for_human",
            "metrics": metrics,
            "report": visual,
            "suggested_decision": decision
}
    # =========================================================
    # ================= HUMAN DECISION ===============================
    # =========================================================

    def finalize_decision(self, decision, mode="HUMAN"):

        logger.info(f"{mode} DECISION → {decision}")

        output = {
            "decision": decision,
            "metrics": self.last_metrics
        }

        if decision == "REJECT":
            output["action"] = "SEND_TO_MESSAGING"
            self._simulate_messaging(output)

        self._save_json("decision.json", output)

        # ================= RESET STATE =================
        self.state.clear_batch()

        logger.info("🔄 System ready for next batch\n==============================================================\n")

        return output

    # =========================================================
    # ================= DECISION LOGIC =========================
    # =========================================================

    def _suggest_decision(self, metrics):

        if metrics["errors"] > self.eval_cfg["max_errors"]:
            return "REJECT"

        if metrics["max_consecutive"] > self.eval_cfg["max_consecutive_errors"]:
            return "REJECT"

        return "ACCEPT "

    # =========================================================
    # ================= MESSAGING ==============================
    # =========================================================

    def _simulate_messaging(self, payload):

        if not self.external_cfg["messaging"]["enabled"]:
            logger.info("Messaging disabled (simulation only)")
            return

        logger.warning("Sending REJECT classifier config to messaging system (SIMULATED)")
        logger.info(json.dumps(payload, indent=2))

    # =========================================================
    # ================= UTIL ===============================
    # =========================================================

    def _save_json(self, filename, data):

        os.makedirs(self.paths_cfg["output_dir"], exist_ok=True)

        path = os.path.join(self.paths_cfg["output_dir"], filename)

        with open(path, "w") as f:
            json.dump(data, f, indent=2)
