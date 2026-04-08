from src.api.json_api import app
from src.config.config_loader import Config
config = Config()
def choose_mode():
    print("\n=== Select Evaluation Mode ===")
    print("1) Human Mode")
    print("2) Testing / Automated Mode")
    while True:
        choice = input("Enter choice: ").strip()

        if choice == "1":
            config["server"]["mode"] = "human"
            break

        elif choice == "2":
            config["server"]["mode"] = "auto"
            break

        else:
            print("Invalid input. Choose 1 or 2.")

    print(f"\nSelected Mode: {config['server']['mode'].upper()}")

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