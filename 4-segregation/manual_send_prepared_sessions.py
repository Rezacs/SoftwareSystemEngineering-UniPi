"""Tests the prepared-session input endpoint by sending one or more local JSON files via HTTP."""

import json
import time
from pathlib import Path

import requests
from src import PREPARED_SESSIONS_ENDPOINT


PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.json"
INPUT_DIR = PROJECT_ROOT / "data" / "input"


def send_prepared_sessions():
    """
    Test the sending of one or more prepared-session JSON files to the
    Segregation System REST endpoint.
    """
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        config = json.load(config_file)

    url = (
        f"http://{config['segregationSystemIpAddress']}:"
        f"{config['segregationSystemPort']}"
        f"{PREPARED_SESSIONS_ENDPOINT}"
    )

    json_files = sorted(INPUT_DIR.glob("prepared_session*.json"))
    if not json_files:
        raise FileNotFoundError(
            f"No prepared-session JSON files found in {INPUT_DIR}"
        )

    for json_filename in json_files:
        with json_filename.open("r", encoding="utf-8") as file:
            json_data = json.load(file)

        response = requests.post(url, json=json_data, timeout=5)
        print(f"{json_filename.name}: {response.status_code} {response.text}")
        time.sleep(1)


if __name__ == "__main__":
    send_prepared_sessions()
    print("Test passed")
