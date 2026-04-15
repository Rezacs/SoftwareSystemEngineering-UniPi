"""Simulation script that sends payloads with varying numbers of classifiers."""

import requests

DESTINATION_URL = "http://127.0.0.1:5005/data"

CLASSIFIER_COUNTS = [1, 2, 3, 4, 5]

HYPERPARAMETERS_POOL = [
    {"classifier_id": "c1", "num_layers": 2, "num_neurons": 16,  "num_iterations": 100},
    {"classifier_id": "c2", "num_layers": 3, "num_neurons": 32,  "num_iterations": 150},
    {"classifier_id": "c3", "num_layers": 4, "num_neurons": 64,  "num_iterations": 200},
    {"classifier_id": "c4", "num_layers": 5, "num_neurons": 128, "num_iterations": 250},
    {"classifier_id": "c5", "num_layers": 6, "num_neurons": 256, "num_iterations": 300},
]

mock_payload = {
    "training_set": [
        {
            "session_id": "s-001", "player_id": 1,
            "skill_overall": 0.8, "social_influence_score": 0.2,
            "injuries_impact_score": 0.1, "label": 4,
        },
        {
            "session_id": "s-002", "player_id": 2,
            "skill_overall": 0.4, "social_influence_score": 0.5,
            "injuries_impact_score": 0.6, "label": 2,
        },
        {
            "session_id": "s-003", "player_id": 3,
            "skill_overall": 0.6, "social_influence_score": 0.3,
            "injuries_impact_score": 0.3, "label": 3,
        },
        {
            "session_id": "s-004", "player_id": 4,
            "skill_overall": 0.2, "social_influence_score": 0.8,
            "injuries_impact_score": 0.4, "label": 1,
        },
        {
            "session_id": "s-005", "player_id": 5,
            "skill_overall": 0.9, "social_influence_score": 0.1,
            "injuries_impact_score": 0.0, "label": 5,
        },
    ],
    "validation_set": [
        {
            "session_id": "s-006", "player_id": 6,
            "skill_overall": 0.7, "social_influence_score": 0.4,
            "injuries_impact_score": 0.2, "label": 4,
        },
        {
            "session_id": "s-007", "player_id": 7,
            "skill_overall": 0.3, "social_influence_score": 0.6,
            "injuries_impact_score": 0.5, "label": 2,
        },
    ],
    "test_set": [
        {
            "session_id": "s-008", "player_id": 8,
            "skill_overall": 0.5, "social_influence_score": 0.5,
            "injuries_impact_score": 0.3, "label": 3,
        },
        {
            "session_id": "s-009", "player_id": 9,
            "skill_overall": 0.1, "social_influence_score": 0.9,
            "injuries_impact_score": 0.8, "label": 1,
        },
    ],
}


def send_payload(n_classifiers: int) -> None:
    """Build a payload with n_classifiers hyperparameter configs and POST it."""
    payload = dict(mock_payload)
    payload["hyperparameters"] = HYPERPARAMETERS_POOL[:n_classifiers]

    print(f"\n{'='*60}")
    print(f"Sending payload — classifiers: {n_classifiers}")
    print(f"{'='*60}")

    try:
        response = requests.post(
            DESTINATION_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if response.status_code == 200:
            print("Success! Data accepted by Development System.")
            print(f"Response: {response.text}")
        else:
            print(f"Failed. Status: {response.status_code}")
            print(f"Detail: {response.text}")
    except requests.exceptions.ConnectionError:
        print("Connection Error: Is the Development System running?")


if __name__ == "__main__":
    for n in CLASSIFIER_COUNTS:
        send_payload(n)