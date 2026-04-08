import requests

DESTINATION_URL = "http://127.0.0.1:5005/data"

def send_mock_payload():
    print(f"Preparing to send mock payload to {DESTINATION_URL}...")

    mock_payload = {
        "training_set": [
            {"session_id": "s-001", "player_id": 1, "skill_overall": 0.8, "social_influence_score": 0.2, "injuries_impact_score": 0.1, "label": 4},
            {"session_id": "s-002", "player_id": 2, "skill_overall": 0.4, "social_influence_score": 0.5, "injuries_impact_score": 0.6, "label": 2},
            {"session_id": "s-003", "player_id": 3, "skill_overall": 0.6, "social_influence_score": 0.3, "injuries_impact_score": 0.3, "label": 3},
            {"session_id": "s-004", "player_id": 4, "skill_overall": 0.2, "social_influence_score": 0.8, "injuries_impact_score": 0.4, "label": 1},
            {"session_id": "s-005", "player_id": 5, "skill_overall": 0.9, "social_influence_score": 0.1, "injuries_impact_score": 0.0, "label": 5},
        ],
        "validation_set": [
            {"session_id": "s-006", "player_id": 6, "skill_overall": 0.7, "social_influence_score": 0.4, "injuries_impact_score": 0.2, "label": 4},
            {"session_id": "s-007", "player_id": 7, "skill_overall": 0.3, "social_influence_score": 0.6, "injuries_impact_score": 0.5, "label": 2},
        ],
        "test_set": [
            {"session_id": "s-008", "player_id": 8, "skill_overall": 0.5, "social_influence_score": 0.5, "injuries_impact_score": 0.3, "label": 3},
            {"session_id": "s-009", "player_id": 9, "skill_overall": 0.1, "social_influence_score": 0.9, "injuries_impact_score": 0.8, "label": 1},
        ],
    }

    try:
        response = requests.post(
            DESTINATION_URL,
            json=mock_payload,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print("✅ Success! Data accepted by Development System.")
            print(f"Response: {response.text}")
        else:
            print(f"❌ Failed. Status: {response.status_code}")
            print(f"Detail: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Is the Development System running?")

if __name__ == "__main__":
    send_mock_payload()