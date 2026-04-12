import requests
import time
import random

# ================= CONFIG =================
EXPERT_URL = "http://127.0.0.1:5007/expert-label"
CLASSIFIER_URL = "http://127.0.0.1:5007/classifier-label"

HEADERS = {
    "Content-Type": "application/json"
}

# ================= VALIDATION =================
def generate_label():
    return random.randint(1, 5)  # valid labels only


def generate_player_id(i):
    return i  # integer only


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
def run_test(num_records=10, delay=0.5):
    """
    num_records: number of player_ids to send
    delay: seconds between requests
    """

    for i in range(1, num_records + 1):

        player_id = generate_player_id(i)

        # generate labels
        expert_label = generate_label()
        classifier_label = generate_label()

        # send expert first
        send_expert_label(player_id, expert_label)

        time.sleep(delay)

        # send classifier
        send_classifier_label(player_id, classifier_label)

        time.sleep(delay)


# ================= ENTRY =================
if __name__ == "__main__":
    run_test(num_records=50, delay=0.3)