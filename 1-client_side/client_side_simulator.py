import pandas as pd
import numpy as np
import requests

def wait_and_send(record, source_file, server_url):
    """Helper function to handle the pause, print, and network request."""
    print(f"\n[Source: {source_file}] - Data for Player ID: {record.get('player_id')}")
    print(f"Payload: {record}")
    
    user_action = input("Press [ENTER] to send this request, or type 'q' to quit: ")
    
    if user_action.strip().lower() == 'q':
        return False  # Signals the main loop to quit

    try:
        # Send as a list containing one dictionary: [ {data} ]
        response = requests.post(server_url, json=record)
        if response.status_code == 200:
            print(f"  -> Success! Server: {response.json()}")
        else:
            print(f"  -> Failed! Status: {response.status_code} - {response.text}")
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the server. Is your Flask app running?")
        return False # Signals the main loop to quit
        
    return True

def stream_synchronized_player_data(csv_files, server_url):
    if len(csv_files) != 3:
        print("Error: This script is designed for exactly 3 CSV files.")
        return

    print("Loading CSV files...")
    dfs = []
    
    # 1. Load all 3 CSVs into memory
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            df = df.replace({np.nan: None}) # Clean NaNs for JSON
            dfs.append(df)
            print(f" -> Loaded '{file}'")
        except FileNotFoundError:
            print(f"Error: File '{file}' not found.")
            return

    df1, df2, df3 = dfs[0], dfs[1], dfs[2]
    file1, file2, file3 = csv_files[0], csv_files[1], csv_files[2]

    print(df3.columns)



    if 'player_id' not in df1.columns:
        print(f"Error: The first CSV ('{file1}') must contain a 'player_id' column.")
        return

    print("\nStarting synchronized row-by-row transmission...\n")

    # 2. Iterate through the FIRST CSV row by row
    for index, row in df1.iterrows():
        current_id = row['player_id']
        
        # Skip empty IDs
        if pd.isna(current_id) or current_id is None:
            continue
            
        print(f"\n==========================================")
        print(f"   Processing Player ID: {current_id}")
        print(f"==========================================")

        # --- STEP A: Send row from CSV 1 ---
        record1 = {
            "player_id" : row['player_id'],
            "skill_overall" :row['overall'],
            "label" : 3
        }
        
        if not wait_and_send(record1, file1, server_url):
            print("Transmission stopped.")
            break

        # --- STEP B: Find and send row from CSV 2 ---
        if 'player_id' in df2.columns:
            match2 = df2[df2['player_id'] == current_id]
            if not match2.empty:
                # Take the first matching row and convert to dictionary
                r2 = match2.iloc[0].to_dict()
                record2={
                    "player_id" : r2['player_id'],
                    "days_missed" :r2['days_missed'],
                    "games_missed" : r2['games_missed']    
                }
                if not wait_and_send(record2, file2, server_url):
                    print("Transmission stopped.")
                    break
            else:
                print(f"\n[Source: {file2}] - No data found for Player {current_id}. Skipping.")

        # --- STEP C: Find and send row from CSV 3 ---
        if 'id_player' in df3.columns:
            match3 = df3[df3['id_player'] == current_id]
            if not match3.empty:
                r3 = match3.iloc[0].to_dict()
                record3 = {
                    "player_id" : r3['id_player'],
                    "number_of_likes" :r3['numberOfLikes'],
                    "number_of_followers" : r3['numberOfFollowers']
                }
                if not wait_and_send(record3, file3, server_url):
                    print("Transmission stopped.")
                    break
            else:
                print(f"\n[Source: {file3}] - No data found for Player {current_id}. Skipping.")

    print("\nFinished processing.")

if __name__ == "__main__":

    SERVER_URL = 'http://127.0.0.1:5001/run'
    
    # The first file in this list drives the main loop
    CSV_FILES = ['../data/inputs/raws_football_db.csv', '../data/inputs/raws_medical_db.csv', '../data/inputs/raws_social_db.csv']
    
    stream_synchronized_player_data(CSV_FILES, SERVER_URL)