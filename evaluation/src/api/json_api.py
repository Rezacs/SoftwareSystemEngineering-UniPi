"""Flask API routes for the evaluation system."""

from flask import Flask, jsonify, request

from src.config.config_loader import Config
from src.core.batch_manager import BatchManager
from src.core.orchestrator import Orchestrator
from src.core.state_manager import StateManager
from src.storage.repository import Repository
from src.storage.sqlite_store import SQLiteStore
from src.utils.logger import logger
from src.utils.system_cleaner import SystemCleaner
from src.validation.schema_validator import SchemaValidator


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
    """Handle expert-labeled input data."""
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
    """Handle classifier-generated label input data."""
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
    """Process a final human review decision."""
    data = request.json
    decision = data.get("decision")

    if decision not in ["ACCEPT", "REJECT"]:
        return jsonify({"error": "Decision must be ACCEPT or REJECT"}), 400

    # ================= APPLY DECISION =================
    result = orchestrator.finalize_decision(decision, mode="HUMAN")
    return jsonify(result)

# =========================================================
# ================= RESET SYSTEM  ================
# =========================================================

@app.route("/reset", methods=["POST"])
def reset():
    """Reset the database and application state. Was useful for testing"""
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
    """Return the current API health status. was useful for testing"""
    return jsonify({
        "status": "running",
        "system": "evaluation"
    })