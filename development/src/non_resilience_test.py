import requests

DESTINATION_URL = "http://127.0.0.1:5005/data"

VALID_PAYLOAD = {
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
    "hyperparameters": [
        {"classifier_id": "manual_alpha", "num_layers": 2, "num_neurons": 16, "num_iterations": 100},
        {"classifier_id": "manual_beta",  "num_layers": 3, "num_neurons": 32, "num_iterations": 150},
    ],
}

# ── D1: Missing set (training, validation or test) ───────────────────────────
# Score 3: learning set discarded, development doesn't start, alert sent

D1_CASES = [
    {
        "description": "D1 — missing training_set",
        "payload": {k: v for k, v in VALID_PAYLOAD.items() if k != "training_set"},
    },
    {
        "description": "D1 — missing validation_set",
        "payload": {k: v for k, v in VALID_PAYLOAD.items() if k != "validation_set"},
    },
    {
        "description": "D1 — missing test_set",
        "payload": {k: v for k, v in VALID_PAYLOAD.items() if k != "test_set"},
    },
]

# ── D2: Malformed learning set (e.g. less labels than rows) ──────────────────
# Score 5: Training/Validation/Testing fails and system crashes

D2_CASES = [
    {
        "description": "D2 — less labels than rows in training_set",
        "payload": {
            **VALID_PAYLOAD,
            "training_set": [
                {"session_id": "s-001", "player_id": 1, "skill_overall": 0.8, "social_influence_score": 0.2, "injuries_impact_score": 0.1, "label": 4},
                {"session_id": "s-002", "player_id": 2, "skill_overall": 0.4, "social_influence_score": 0.5, "injuries_impact_score": 0.6},  # missing label
                {"session_id": "s-003", "player_id": 3, "skill_overall": 0.6, "social_influence_score": 0.3, "injuries_impact_score": 0.3},  # missing label
                {"session_id": "s-004", "player_id": 4, "skill_overall": 0.2, "social_influence_score": 0.8, "injuries_impact_score": 0.4, "label": 1},
                {"session_id": "s-005", "player_id": 5, "skill_overall": 0.9, "social_influence_score": 0.1, "injuries_impact_score": 0.0, "label": 5},
            ],
        },
    },
    {
        "description": "D2 — less labels than rows in validation_set",
        "payload": {
            **VALID_PAYLOAD,
            "validation_set": [
                {"session_id": "s-006", "player_id": 6, "skill_overall": 0.7, "social_influence_score": 0.4, "injuries_impact_score": 0.2, "label": 4},
                {"session_id": "s-007", "player_id": 7, "skill_overall": 0.3, "social_influence_score": 0.6, "injuries_impact_score": 0.5},  # missing label
            ],
        },
    },
    {
        "description": "D2 — less labels than rows in test_set",
        "payload": {
            **VALID_PAYLOAD,
            "test_set": [
                {"session_id": "s-008", "player_id": 8, "skill_overall": 0.5, "social_influence_score": 0.5, "injuries_impact_score": 0.3, "label": 3},
                {"session_id": "s-009", "player_id": 9, "skill_overall": 0.1, "social_influence_score": 0.9, "injuries_impact_score": 0.8},  # missing label
            ],
        },
    },
]
# ── D3: Too few records ───────────────────────────────────────────────────────
# Score 5: system trains only very bad classifiers, might remain stuck in validation loop

D3_CASES = [
    {
        "description": "D3 — too few records in training_set",
        "payload": {
            **VALID_PAYLOAD,
            "training_set": [
                {"session_id": "s-001", "player_id": 1, "skill_overall": 0.8, "social_influence_score": 0.2, "injuries_impact_score": 0.1, "label": 4},
            ],
        },
    },
    {
        "description": "D3 — too few records in validation_set",
        "payload": {
            **VALID_PAYLOAD,
            "validation_set": [
                {"session_id": "s-006", "player_id": 6, "skill_overall": 0.7, "social_influence_score": 0.4, "injuries_impact_score": 0.2, "label": 4},
            ],
        },
    },
    {
        "description": "D3 — too few records in both training and validation",
        "payload": {
            **VALID_PAYLOAD,
            "training_set": [
                {"session_id": "s-001", "player_id": 1, "skill_overall": 0.8, "social_influence_score": 0.2, "injuries_impact_score": 0.1, "label": 4},
            ],
            "validation_set": [
                {"session_id": "s-006", "player_id": 6, "skill_overall": 0.7, "social_influence_score": 0.4, "injuries_impact_score": 0.2, "label": 4},
            ],
        },
    },
]

# ── D4: Malformed hyperparameter input ───────────────────────────────────────
# Score 3: error in input is detected, alert is sent

D4_CASES = [
    {
        "description": "D4 — missing classifier_id in hyperparameters",
        "payload": {
            **VALID_PAYLOAD,
            "hyperparameters": [
                {"num_layers": 2, "num_neurons": 16, "num_iterations": 100},
            ],
        },
    },
    {
        "description": "D4 — wrong types in hyperparameters",
        "payload": {
            **VALID_PAYLOAD,
            "hyperparameters": [
                {"classifier_id": "manual_alpha", "num_layers": "two", "num_neurons": "sixteen", "num_iterations": "hundred"},
            ],
        },
    },
    {
        "description": "D4 — negative values in hyperparameters",
        "payload": {
            **VALID_PAYLOAD,
            "hyperparameters": [
                {"classifier_id": "manual_alpha", "num_layers": -2, "num_neurons": -16, "num_iterations": -100},
            ],
        },
    },
    {
        "description": "D4 — empty hyperparameters list",
        "payload": {
            **VALID_PAYLOAD,
            "hyperparameters": [],
        },
    },
]

def send_case(case: dict) -> None:
    print(f"\n{'='*60}")
    print(f"Sending: {case['description']}")
    print(f"{'='*60}")
    try:
        response = requests.post(
            DESTINATION_URL,
            json=case["payload"],
            headers={"Content-Type": "application/json"},
        )
        print(f"Status : {response.status_code}")
        print(f"Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Is the Development System running?")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("NON-RESILIENCY TEST — DEVELOPMENT SYSTEM")
    print("="*60)

    print("\n--- D1: Missing set cases (expected: alert sent, score 3) ---")
    for case in D1_CASES:
        send_case(case)

    print("\n--- D2: Malformed learning set cases (expected: system crash, score 5) ---")
    for case in D2_CASES:
        send_case(case)

    print("\n--- D3: Too few records (expected: stuck in validation loop, score 5) ---")
    for case in D3_CASES:
        send_case(case)

    print("\n--- D4: Malformed hyperparameter input (expected: alert sent, score 3) ---")
    for case in D4_CASES:
        send_case(case)