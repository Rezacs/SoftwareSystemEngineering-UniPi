from flask import Flask, request, jsonify

from src.config.config_loader import Config
from src.validation.schema_validator import SchemaValidator
from src.storage.sqlite_store import SQLiteStore
from src.storage.repository import Repository
from src.core.batch_manager import BatchManager
from src.core.state_manager import StateManager
from src.core.orchestrator import Orchestrator
from src.utils.system_cleaner import SystemCleaner

from src.utils.logger import logger


app = Flask(__name__)

# ================= LOAD CONFIG =================
config = Config()

# ================= CLEAN SYSTEM =================
cleaner = SystemCleaner(config)
cleaner.clean_all()

# ================= INIT COMPONENTS =================
validator = SchemaValidator()

store = SQLiteStore(config["paths"]["database"])
repo = Repository(store)

batch_mgr = BatchManager(config["evaluation"]["batch_size"])
state = StateManager()

orchestrator = Orchestrator(repo, batch_mgr, config, state)


# =========================================================
# ================= EXPERT LABEL ===========================
# =========================================================

@app.route("/expert-label", methods=["POST"])
def expert_label():

    data = request.json
    data["source"] = "expert"

    try:
        validator.validate(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(orchestrator.process(data))


# =========================================================
# ================= CLASSIFIER LABEL =======================
# =========================================================

@app.route("/classifier-label", methods=["POST"])
def classifier_label():

    data = request.json
    data["source"] = "classifier"

    try:
        validator.validate(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(orchestrator.process(data))


# =========================================================
# ================= HUMAN DECISION =========================
# =========================================================

@app.route("/human-decision", methods=["POST"])
def human_decision():

    data = request.json
    decision = data.get("decision")

    if decision not in ["ACCEPT", "REJECT"]:
        return jsonify({"error": "Decision must be ACCEPT or REJECT"}), 400

    # ================= APPLY DECISION =================
    result = orchestrator.finalize_decision(decision, mode="HUMAN")

   # logger.info("🔄 Resetting system for next batch...")

    # ================= RESET STATE =================
    #state.clear_batch()

    return jsonify(result)


# =========================================================
# ================= RESET SYSTEM  ================
# =========================================================

@app.route("/reset", methods=["POST"])
def reset():

    logger.warning("⚠️ Manual system reset triggered")

    repo.clear()
    state.reset()

    return jsonify({
        "status": "system_reset",
        "message": "Database cleared and state reset"
    })


# =========================================================
# ================= HEALTH CHECK ===========================
# =========================================================

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "running",
        "system": "evaluation"
    })