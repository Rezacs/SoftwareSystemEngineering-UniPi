import requests
import concurrent.futures
import time
import random

# Target endpoint
URL = "http://127.0.0.1:8001/evaluation"

# Test parameters
TOTAL_REQUESTS = 200      # Total number of labels to send
CONCURRENT_WORKERS = 20   # How many requests to send at the EXACT same time

def send_dummy_data(request_id):
    """Simulates a single system sending a label."""
    # Generate random valid data to bypass the JSON schema filter
    dummy_data = {
        "player_id": f"PLAYER_{random.randint(100, 999)}",
        "rating": random.randint(1, 5),
        "source": random.choice(["classifier", "expert"])
    }
    
    try:
        # Send the POST request
        response = requests.post(URL, json=dummy_data, timeout=5)
        return response.status_code
    except Exception as e:
        return "Failed to connect"

def run_stress_test():
    print(f"🚀 Starting Stress Test...")
    print(f"Sending {TOTAL_REQUESTS} requests with {CONCURRENT_WORKERS} concurrent workers.\n")
    
    start_time = time.time()
    
    # This block fires off the requests simultaneously 
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        results = list(executor.map(send_dummy_data, range(TOTAL_REQUESTS)))
        
    end_time = time.time()
    duration = end_time - start_time
    
    # Tally the results (Your server returns 201 for success)
    successes = results.count(201) + results.count(200)
    failures = TOTAL_REQUESTS - successes
    
    print("====================================================")
    print("STRESS TEST RESULTS (ELASTICITY PROOF)")
    print("====================================================")
    print(f"Total Time Taken:      {duration:.2f} seconds")
    print(f"Throughput:            {TOTAL_REQUESTS / duration:.2f} requests per second")
    print(f"Successful Requests:   {successes} ({successes/TOTAL_REQUESTS*100:.1f}%)")
    print(f"Failed/Dropped:        {failures}")
    print("====================================================")

if __name__ == "__main__":
    run_stress_test()