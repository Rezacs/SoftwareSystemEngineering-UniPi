import requests

url = "http://127.0.0.1:8001/evaluation"

# Now perfectly matching: 
# 1. 'source' must be 'expert' or 'classifier'
# 2. 'rating' must be between 1 and 5
dummy_data = {
    "player_id": "PLAYER_007",
    "rating": 5, 
    "source": "expert" 
}

print(f"Sending dummy data to {url}...")

try:
    response = requests.post(url, json=dummy_data)
    print(f"Status Code: {response.status_code}")
    print(f"Server Response: {response.text}")
except Exception as e:
    print(f"Connection failed: {e}")