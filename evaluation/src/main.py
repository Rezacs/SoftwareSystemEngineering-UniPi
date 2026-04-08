from src.api.json_api import app
from src.config.config_loader import Config
import json
import os


# def load_config():
#     config_path = os.path.join("data", "config.json")
#     with open(config_path, "r") as f:
#         return json.load(f)


if __name__ == "__main__":

    config = Config()

    host = config["server"]["host"]
    port = config["server"]["port"]

    print("\n=== Evaluation System Starting ===")
    print(f"Server running on: http://{host}:{port}")
    print("=================================\n")

    app.run(
        host=host,
        port=port,
        debug=False  #False for stability
    )