import requests
import json

def send_payload(payload, server_url):
    """Helper function to handle the pause, print, and network request."""
    print(f"\nPayload ready to send:")
    print(json.dumps(payload, indent=4))
    
    # Wait for the user to press Enter before sending
    user_action = input("\nPress [ENTER] to send this request, or type 'c' to cancel: ")
    
    if user_action.strip().lower() == 'c':
        print(" -> Canceled sending. Returning to menu.")
        return True # Return True to keep the main loop running

    try:
        response = requests.post(server_url, json=payload)
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
                "UUID": "b944d261-41ac-4ff0-86b6-6fbaf3a876a2",
                "missing_created_at" : None,
                "records": [
                    {'ID': 16, 'player_id': 6, 'skill_overall': 82.0, 'number_of_likes': -1, 'number_of_followers': -1, 'days_missed': -1, 'games_missed': -1, 'label': 3, 'UUID': 'b944d261-41ac-4ff0-86b6-6fbaf3a876a2'},
                    {'ID': 7, 'player_id': 3, 'skill_overall': 90.0, 'number_of_likes': 425, 'number_of_followers': 901, 'days_missed': 188, 'games_missed': 43, 'label': 3, 'UUID': 'b944d261-41ac-4ff0-86b6-6fbaf3a876a2'},
                    {'ID': 4, 'player_id': 2, 'skill_overall': 90.0, 'number_of_likes': 87, 'number_of_followers': 306, 'days_missed': 256, 'games_missed': 34, 'label': 3, 'UUID': 'b944d261-41ac-4ff0-86b6-6fbaf3a876a2'},
                    {'ID': 1, 'player_id': 1, 'skill_overall': 89.0, 'number_of_likes': 967, 'number_of_followers': 514, 'days_missed': 268, 'games_missed': 61, 'label': 3, 'UUID': 'b944d261-41ac-4ff0-86b6-6fbaf3a876a2'}
                ]
            }
        },
        {
            "description": "Missing Label",
            "data": {
                "UUID": "b944d261-41ac-4ff0-86b6-6fbaf3a876a2",
                "created_at" : "2026-04-02T16:50:03.202063",
                "records": [
                    {'ID': 16, 'player_id': 6, 'skill_overall': 82, 'number_of_likes': -1, 'number_of_followers': -1, 'days_missed': -1, 'games_missed': -1,"label" : None, 'UUID': 'b944d261-41ac-4ff0-86b6-6fbaf3a876a2'}
                ]
            }
        },
        {
            "description": "Missing values",
            "data": {
                "UUID": "b944d261-41ac-4ff0-86b6-6fbaf3a876a2",
                "created_at" : "2026-04-02T16:50:03.202063",
                "records": [
                    {'ID': 16, 'player_id': 0, 'skill_overall': 90, 'number_of_likes': 20, 'number_of_followers': 20, 'days_missed': 20, 'games_missed': 20, 'label': 3, 'UUID': 'b944d261-41ac-4ff0-86b6-6fbaf3a876a2'},
                    {'ID': 7, 'player_id': 3, 'skill_overall': None, 'number_of_likes': 425, 'number_of_followers': 901, 'days_missed': 188, 'games_missed': 43, 'label': 3, 'UUID': 'b944d261-41ac-4ff0-86b6-6fbaf3a876a2'},
                    {'ID': 4, 'player_id': 22, 'skill_overall': None, 'number_of_likes': 87, 'number_of_followers': 306, 'days_missed': 256, 'games_missed': 34, 'label': 3, 'UUID': 'b944d261-41ac-4ff0-86b6-6fbaf3a876a2'},
                    {'ID': 1, 'player_id': 1, 'skill_overall': 10, 'number_of_likes': 967, 'number_of_followers': 514, 'days_missed': 268, 'games_missed': 61, 'label': 3, 'UUID': 'b944d261-41ac-4ff0-86b6-6fbaf3a876a2'}
                ]
            }
        },
        {
            "description": "Outliers",
            "data": {
                "UUID": "b944d261-41ac-4ff0-86b6-6fbaf3a876a2",
                "created_at" : "2026-04-02T16:50:03.202063",
                "records": [
                    {'ID': 16, 'player_id': -99, 'skill_overall': 2000, 'number_of_likes': -1, 'number_of_followers': -1, 'days_missed': -1, 'games_missed': -1, 'label': 3, 'UUID': 'b944d261-41ac-4ff0-86b6-6fbaf3a876a2'},
                    {'ID': 7, 'player_id': 3, 'skill_overall': -2, 'number_of_likes': 425, 'number_of_followers': 901, 'days_missed': 188, 'games_missed': 43, 'label': 3, 'UUID': 'b944d261-41ac-4ff0-86b6-6fbaf3a876a2'},
                    {'ID': 4, 'player_id': -4, 'skill_overall': -5, 'number_of_likes': 87, 'number_of_followers': 306, 'days_missed': 256, 'games_missed': 34, 'label': 3, 'UUID': 'b944d261-41ac-4ff0-86b6-6fbaf3a876a2'},
                    {'ID': 1, 'player_id': 1, 'skill_overall': 123, 'number_of_likes': 967, 'number_of_followers': 514, 'days_missed': 268, 'games_missed': 61, 'label': 3, 'UUID': 'b944d261-41ac-4ff0-86b6-6fbaf3a876a2'}
                ]
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
            print("\n❌ Invalid choice. Please enter a valid number from the list.")
            continue

        # 3. Retrieve the selected JSON and pass it to the sending function
        selected_index = int(choice)
        selected_payload = hardcoded_options[selected_index]['data']
        
        if not isinstance(selected_payload,list):
            print(f"\n--- Loading: {hardcoded_options[selected_index]['description']} ---")
            send_payload(selected_payload, server_url)
        else:
            for p in selected_payload:
                print(f"\n--- Loading: {hardcoded_options[selected_index]['description']} ---")
                send_payload(p, server_url)


if __name__ == "__main__":
    SERVER_URL = 'http://127.0.0.1:5002/run'
    interactive_json_menu(SERVER_URL)