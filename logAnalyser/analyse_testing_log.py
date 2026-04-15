import pandas as pd
import os
import json

def process_logs():
    # Configuration
    folder_name = "Non Responsiveness Test - Development Phase"
    sizes = [32, 64, 128, 256, 5]
    versions = [1, 2, 3, 5]
    
    # Path handling: check local or parent directory
    base_path = ""
    if os.path.exists(folder_name):
        base_path = folder_name
    elif os.path.exists(os.path.join("..", folder_name)):
        base_path = os.path.join("..", folder_name)
    else:
        print(f"Error: Folder '{folder_name}' not found.")
        return

    for size in sizes:
        for version in versions:
            file_name = f"dev-test_{size}_{version}.csv"
            file_path = os.path.join(base_path, file_name)
            
            if os.path.exists(file_path):
                try:
                    print(f"Processing: {file_name}...")
                    df = pd.read_csv(file_path)

                    # Group and calculate metrics
                    summary = df.groupby('process')['latency_s'].agg(
                        occurrences='count',
                        avg_latency='mean'
                    ).reset_index()

                    # Create JSON filename (e.g., dev-test_32_1.json)
                    json_name = file_name.replace(".csv", ".json")
                    
                    # Convert to list of dicts and save
                    result_data = summary.to_dict(orient='records')
                    with open(json_name, 'w') as f:
                        json.dump(result_data, f, indent=4)
                    
                    print(f"  -> Saved to {json_name}")

                except Exception as e:
                    print(f"  -> Error processing {file_name}: {e}")
            else:
                print(f"Skipping: {file_name} (File not found)")

if __name__ == "__main__":
    process_logs()