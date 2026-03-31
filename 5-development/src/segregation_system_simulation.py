import requests
import json
import time

DESTINATION_URL = "http://127.0.0.1:5000/data/internal/received_data.json"

def send_mock_payload():
    print(f" Preparing to send mock payload to {DESTINATION_URL}...")
    
    # This structure matches your 'parse_learning_set' and 'parse_hyper_parameters' logic
    mock_payload = {
        "hyper_parameters": [
            {"classifier_id": "manual_alpha", "num_layers": 2, "num_neurons": 16, "num_iterations": 100},
            {"classifier_id": "manual_beta", "num_layers": 3, "num_neurons": 32, "num_iterations": 150}
        ],
        "learning_set": {
            "training_set": [
                {"UUID": "1", "idPlayer": "P1", "skillOverall": 0.8, "socialInfluence": 0.2, "injuriesImpact": 0.1, "label": 4},
                {"UUID": "2", "idPlayer": "P2", "skillOverall": 0.4, "socialInfluence": 0.5, "injuriesImpact": 0.6, "label": 2}
            ],
            "validation_set": [
                {"UUID": "3", "idPlayer": "P3", "skillOverall": 0.9, "socialInfluence": 0.1, "injuriesImpact": 0.0, "label": 5}
            ],
            "test_set": [
                {"UUID": "4", "idPlayer": "P4", "skillOverall": 0.1, "socialInfluence": 0.1, "injuriesImpact": 0.9, "label": 1}
            ]
        },
        "config": {
            "overfitting_threshold": 0.25,
            "generalization_threshold": 0.45,
            "max_outer_iterations": 2
        }
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
            print(f"❌ Failed. Server returned status: {response.status_code}")
            print(f"Detail: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Is your Development System actually running and listening?")

if __name__ == "__main__":
    # Give the user a moment to switch windows if needed
    send_mock_payload()