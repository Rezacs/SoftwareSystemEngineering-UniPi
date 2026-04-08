import requests

BASE_URL = "http://127.0.0.1:5000"

players = [
    ("PLAYER_01", 4, 4),
    ("PLAYER_02", 3, 3),
    ("PLAYER_03", 5, 2),
    ("PLAYER_04", 2, 2),
    ("PLAYER_05", 3, 4),
    ("PLAYER_06", 4, 4),
    ("PLAYER_07", 1, 2),
    ("PLAYER_08", 3, 3),
    ("PLAYER_09", 4, 4),
]

for pid, expert, classifier in players:

    # Send expert label
    requests.post(f"{BASE_URL}/expert-label", json={
        "player_id": pid,
        "label": expert
    })

    # Send classifier label
    response = requests.post(f"{BASE_URL}/classifier-label", json={
        "player_id": pid,
        "label": classifier
    })

    print(response.json())