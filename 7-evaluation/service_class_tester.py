import requests
import time
import random
import csv
import os

URL = "http://127.0.0.1:8001/evaluation"
TOTAL_PAIRS_TO_TEST = 20

def run_service_test():
    print("Starting Service Class Automated Testing...")
    log_data = []

    for i in range(1, TOTAL_PAIRS_TO_TEST + 1):
        player_id = f"PLAYER_TEST_{i}"
        
        # Generate random dummy ratings
        classifier_rating = random.randint(1, 5)
        expert_rating = random.randint(1, 5)

        # 1. Simulate Classification System Sending Data
        start_time_classifier = time.time()
        requests.post(URL, json={"player_id": player_id, "rating": classifier_rating, "source": "classifier"})
        end_time_classifier = time.time()

        # 2. Simulate Ingestion System Sending Data 
        # (This triggers the report generation and simulated decision!)
        start_time_expert = time.time()
        requests.post(URL, json={"player_id": player_id, "rating": expert_rating, "source": "expert"})
        end_time_expert = time.time()

        # Calculate Durations
        duration_classifier = end_time_classifier - start_time_classifier
        duration_expert = end_time_expert - start_time_expert
        total_pipeline_duration = duration_classifier + duration_expert

        # Append to log
        log_data.append([
            player_id,
            start_time_classifier,
            end_time_classifier,
            duration_classifier,
            start_time_expert,
            end_time_expert,
            duration_expert,
            total_pipeline_duration
        ])

        print(f"Processed {player_id} in {total_pipeline_duration:.4f} seconds.")

    # PARADIGM 7: Generate CSV Timestamp Log
    csv_filename = "testing_logs.csv"
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            "PlayerID", 
            "Classifier_Start_Timestamp", "Classifier_End_Timestamp", "Classifier_Duration_Sec", 
            "Expert_Start_Timestamp", "Expert_End_Timestamp", "Expert_Duration_Sec",
            "Total_Pipeline_Duration_Sec"
        ])
        writer.writerows(log_data)

    print("====================================================")
    print(f"✅ Testing complete. Logs saved to {os.path.abspath(csv_filename)}")
    print("You can now open this CSV in Excel/Spreadsheet to generate your Elasticity plots!")
    print("====================================================")

if __name__ == "__main__":
    run_service_test()