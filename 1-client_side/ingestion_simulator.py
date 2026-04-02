import requests
import json

def send_payload_in_loop(ip, port, endpoint="/upload"):
    # Build the full URL
    url = f"http://{ip}:{port}{endpoint}"
    
    # Your specific JSON payload
    payload = {
        "UUID": "b944d261-41ac-4ff0-86b6-6fbaf3a876a2",
        "created_at": "2026-04-02T16:50:03.202063",
        "records": [
            {'ID': 16, 'player_id': 6, 'skill_overall': 82.0, 'number_of_likes': -1, 'number_of_followers': -1, 'days_missed': -1, 'games_missed': -1, 'label': 3, 'UUID': 'b944d261-41ac-4ff0-86b6-6fbaf3a876a2'},
            {'ID': 13, 'player_id': 5, 'skill_overall': 82.0, 'number_of_likes': 662, 'number_of_followers': 1000, 'days_missed': 430, 'games_missed': 59, 'label': 3, 'UUID': 'b944d261-41ac-4ff0-86b6-6fbaf3a876a2'},
            {'ID': 10, 'player_id': 4, 'skill_overall': 90.0, 'number_of_likes': 648, 'number_of_followers': 183, 'days_missed': 202, 'games_missed': 35, 'label': 3, 'UUID': 'b944d261-41ac-4ff0-86b6-6fbaf3a876a2'},
            {'ID': 7, 'player_id': 3, 'skill_overall': 90.0, 'number_of_likes': 425, 'number_of_followers': 901, 'days_missed': 188, 'games_missed': 43, 'label': 3, 'UUID': 'b944d261-41ac-4ff0-86b6-6fbaf3a876a2'},
            {'ID': 4, 'player_id': 2, 'skill_overall': 90.0, 'number_of_likes': 87, 'number_of_followers': 306, 'days_missed': 256, 'games_missed': 34, 'label': 3, 'UUID': 'b944d261-41ac-4ff0-86b6-6fbaf3a876a2'},
            {'ID': 1, 'player_id': 1, 'skill_overall': 89.0, 'number_of_likes': 967, 'number_of_followers': 514, 'days_missed': 268, 'games_missed': 61, 'label': 3, 'UUID': 'b944d261-41ac-4ff0-86b6-6fbaf3a876a2'}
        ]
    }

    print(f"Target URL configured as: {url}")
    print("Ready to send payload.")

    while True:
        # Wait for user input
        user_input = input("\nPress [ENTER] to send the payload, or type 'q' to quit: ")
        
        if user_input.strip().lower() == 'q':
            print("Exiting sender.")
            break
            
        print(f"Sending POST request to {url}...")
        
        try:
            # Send the request
            response = requests.post(url, json=payload)
            
            # Print the results
            print(f"Status Code: {response.status_code}")
            try:
                print(f"Response: {response.json()}")
            except json.JSONDecodeError:
                print(f"Response (Raw text): {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("Error: Connection refused. Is the receiving server running and listening on that IP/Port?")

if __name__ == "__main__":
    # --- CONFIGURATION ---
    TARGET_IP = "127.0.0.1"   # Change to your server's IP
    TARGET_PORT = "5002"      # Change to your server's Port
    TARGET_ENDPOINT = "/run"  # Change to your specific API route
    
    send_payload_in_loop(TARGET_IP, TARGET_PORT, TARGET_ENDPOINT)