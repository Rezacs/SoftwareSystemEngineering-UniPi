import requests
import json

# The URL of your running server
url = "http://127.0.0.1:8001/evaluation"

# Dummy player data mimicking what the 'previous system' would send
dummy_data = {
    "player_id": "PLAYER_007",
    "name": "Cristiano Rover",
    "metrics": {
        "speed": 90,
        "stamina": 85,
        "precision": 88
    },
    "metadata": {
        "source": "Match_Scanner_v1",
        "timestamp": "2026-03-29T16:30:00"
    }
}

print(f"Sending dummy data to {url}...")

try:
    response = requests.post(url, json=dummy_data)
    print(f"Status Code: {response.status_code}")
    print(f"Server Response: {response.text}")
except Exception as e:
    print(f"Error connecting to server: {e}")