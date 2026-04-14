import requests
import time
import json
import argparse
from pathlib import Path

# ================= CONFIG =================
EXPERT_URL = "http://127.0.0.1:5007/expert-label"
CLASSIFIER_URL = "http://127.0.0.1:5007/classifier-label"

HEADERS = {
    "Content-Type": "application/json"
}

# ================= INPUT LOADER =================
def load_pairs_from_file(pairs_path):
    """
    Expected JSON format:
    [
      {"player_id": 1, "expert": 4, "classifier": 5},
      ...
    ]
    """
    path = Path(pairs_path)
    if not path.is_file():
        raise FileNotFoundError(f"Pairs file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        pairs = json.load(f)

    if not isinstance(pairs, list):
        raise ValueError("Pairs file must contain a JSON list")

    validated = []
    for idx, item in enumerate(pairs):
        if not isinstance(item, dict):
            raise ValueError(f"Item {idx} is not an object")

        missing = [k for k in ["player_id", "expert", "classifier"] if k not in item]
        if missing:
            raise ValueError(f"Item {idx} missing keys: {missing}")

        validated.append((item["player_id"], item["expert"], item["classifier"]))

    return validated


# ================= SEND FUNCTIONS =================
def send_expert_label(player_id, label):
    payload = {
        "player_id": player_id,
        "label": label
    }

    try:
        response = requests.post(EXPERT_URL, json=payload, headers=HEADERS)
        print(f"[EXPERT] {payload} → {response.status_code} | {response.json()}")
    except Exception as e:
        print(f"[EXPERT ERROR] {e}")


def send_classifier_label(player_id, label):
    payload = {
        "player_id": player_id,
        "label": label
    }

    try:
        response = requests.post(CLASSIFIER_URL, json=payload, headers=HEADERS)
        print(f"[CLASSIFIER] {payload} → {response.status_code} | {response.json()}")
    except Exception as e:
        print(f"[CLASSIFIER ERROR] {e}")


# ================= MAIN TEST =================
def run_test(pairs, delay=0.5):
    """
    pairs: list of tuples (player_id, expert_label, classifier_label)
    delay: seconds between requests
    """

    for player_id, expert_label, classifier_label in pairs:

        # send expert first
        send_expert_label(player_id, expert_label)

        time.sleep(delay)

        # send classifier
        send_classifier_label(player_id, classifier_label)

        time.sleep(delay)


# ================= ENTRY =================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Send explicit expert/classifier label pairs to Evaluation endpoints"
    )
    parser.add_argument(
        "--pairs-file",
        required=True,
        help="Path to JSON file containing label pairs (player_id, expert, classifier)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.3,
        help="Delay in seconds between expert and classifier sends"
    )
    args = parser.parse_args()

    input_pairs = load_pairs_from_file(args.pairs_file)
    run_test(input_pairs, delay=args.delay)