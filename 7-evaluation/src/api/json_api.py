from flask import Flask, request, jsonify

from config.config_loader import Config
from validation.schema_validator import SchemaValidator
from storage.sqlite_store import SQLiteStore
from storage.repository import Repository
from core.batch_manager import BatchManager
from core.state_manager import StateManager
from core.orchestrator import Orchestrator

from utils.logger import logger


app = Flask(__name__)

# ================= LOAD CONFIG =================
config = Config()

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

    if decision not in ["GOOD", "BAD"]:
        return jsonify({"error": "Decision must be GOOD or BAD"}), 400

    # ================= APPLY DECISION =================
    result = orchestrator.human_decision(decision)

    logger.info("🔄 Resetting system for next batch...")

    # ================= RESET STATE =================
    state.clear_batch()

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


# =========================================================
# ================= ENTRY POINT ============================
# =========================================================

if __name__ == "__main__":
    print("\n=== Evaluation System Starting ===")
    print(f"Server running on: http://{config['system']['host']}:{config['system']['port']}")
    print("=================================\n")

    app.run(
        host=config["system"]["host"],
        port=config["system"]["port"],
        debug=False
    )