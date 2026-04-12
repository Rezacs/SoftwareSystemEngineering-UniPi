from src.api.json_api import app
from src.config.config_loader import Config
import json
from pathlib import Path

config = Config()

def choose_mode():
    GENERAL_CONFIG = Path(__file__).resolve().parents[2] / "config" / "GeneralConfig.json"

    with open(GENERAL_CONFIG, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    choice = str(cfg["evaluation"]["mode"])

if __name__ == "__main__":
    choose_mode()
    
    host = config["server"]["host"]
    port = config["server"]["port"]

    print("\n=== Evaluation System Starting ===")
    print(f"Server running on: http://{host}:{port}")
    print("=================================\n")

    #to suppress Flask's default logging
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    app.run(
        host=host,
        port=port,
        debug=False  #False for stability
    )