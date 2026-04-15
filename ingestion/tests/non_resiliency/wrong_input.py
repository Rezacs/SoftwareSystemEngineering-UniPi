import json

import requests


def send_payload(payload, server_url):
    """Helper function to handle the pause, print, and network request."""
    print("\nPayload ready to send:")
    print(json.dumps(payload, indent=4))

    # Wait for the user to press Enter before sending
    user_action = input("\nPress [ENTER] to send this request, or type 'c' to cancel: ")

    if user_action.strip().lower() == 'c':
        print(" -> Canceled sending. Returning to menu.")
        return True  # Return True to keep the main loop running

    try:
        response = requests.post(server_url, json=payload, timeout=10)
        if response.status_code == 200:
            # Safely try to parse JSON response, fallback to text if not JSON
            try:
                server_response = response.json()
            except ValueError:
                server_response = response.text
            print(f"  -> Success! Server: {server_response}")
        else:
            print(f"  -> Failed! Status: {response.status_code} - {response.text}")

    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the server. Is your Flask app running?")

    return True


def interactive_json_menu(server_url):
    """Displays a menu of hardcoded JSONs for the user to select and send."""

    # 1. Define your hardcoded JSONs here
    hardcoded_options = [
        {
            "description": "Invalid json schema",
            "data": {
                "player_id": [101, 2],
                "skill_overall": [85, 0],
                "label": {"a": 3}
            }
        },
        {
            "description": "Unexpected key/values",
            "data": {
                "player_id": 100,
                "abc": 101,
                "cd": 12,
                "aa": 2
            }
        },
        {
            "description": "Missing Label",
            "data": {
                "player_id": 101
            }
        },
        {
            "description": "2 Labels same player Id",
            "data": [{
                "player_id": 101,
                "label": 5
            },
                {
                    "player_id": 101,
                    "label": 3
                }]
        },
        {
            "description": "Record with all missing values",
            "data": {
                "player_id": 1,
                "number_of_likes": None,
                "number_of_followers": None
            }
        },
        {
            "description": "Edge Case (Missing Player ID)",
            "data": {
                "player_id": None,
                "skill_overall": 50,
                "label": 1
            }
        },
        {
            "description": "Outliers",
            "data": {
                "player_id": 2,
                "skill_overall": 200,
                "label": 8
            }
        }
    ]

    print("\nStarting Interactive JSON Sender...")

    # 2. Main interactive loop
    while True:
        print("\n==========================================")
        print(" Select a payload to send:")
        print("==========================================")

        for i, option in enumerate(hardcoded_options):
            print(f" [{i}] - {option['description']}")

        print(" [q] - Quit")
        print("==========================================")

        # Wait for a number
        choice = input("Enter a number (or 'q' to quit): ").strip().lower()

        if choice == 'q':
            print("Exiting program. Goodbye!")
            break

        # Validate the input
        if not choice.isdigit() or not (0 <= int(choice) < len(hardcoded_options)):
            print("\nInvalid choice. Please enter a valid number from the list.")
            continue

        # 3. Retrieve the selected JSON and pass it to the sending function
        selected_index = int(choice)
        selected_payload = hardcoded_options[selected_index]['data']

        if not isinstance(selected_payload, list):
            print(f"\n--- Loading: {hardcoded_options[selected_index]['description']} ---")
            send_payload(selected_payload, server_url)
        else:
            for p in selected_payload:
                print(f"\n--- Loading: {hardcoded_options[selected_index]['description']} ---")
                send_payload(p, server_url)


if __name__ == "__main__":
    SERVER_URL = 'http://127.0.0.1:5001/run'
    interactive_json_menu(SERVER_URL)
