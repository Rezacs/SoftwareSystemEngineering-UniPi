import pandas as pd
import glob
import re
import matplotlib.pyplot as plt
import os

# --- CONFIGURATION ---
FILE_PATTERN = "dev-test_*.json"

def aggregate_data():
    all_data = []
    json_files = glob.glob(FILE_PATTERN)
    
    if not json_files:
        print("No JSON files found! Please run the processing script first.")
        return

    for file in json_files:
        match = re.search(r"dev-test_(\d+)_(\d+).json", file)
        if match:
            size = int(match.group(1))
            version = int(match.group(2))
            
            temp_df = pd.read_json(file)
            temp_df['neurons'] = size
            temp_df['sublayers'] = version
            all_data.append(temp_df)

    full_df = pd.concat(all_data, ignore_index=True)

    # 1. TERMINAL TABLE
    summary = full_df.groupby('process').agg({
        'occurrences': 'mean',
        'avg_latency': 'mean'
    }).reset_index()

    total_occ = summary['occurrences'].sum()
    summary['% of Occurrences'] = (summary['occurrences'] / total_occ) * 100
    
    summary.columns = ['Process (ID)', 'Avg. Occurrences', 'Avg. Latency (s)', '% of Occurrences']
    tot_row = pd.DataFrame({
        'Process (ID)': ['TOT'],
        'Avg. Occurrences': [summary['Avg. Occurrences'].sum()],
        'Avg. Latency (s)': [summary['Avg. Latency (s)'].mean()],
        '% of Occurrences': [100.0]
    })
    
    table_df = pd.concat([summary, tot_row], ignore_index=True)
    print("\n--- GLOBAL AGGREGATED METRICS ---")
    print(table_df.to_string(index=False, formatters={'Avg. Latency (s)': '{:,.4f}'.format, '% of Occurrences': '{:,.2f}%'.format}))

    # 2. PLOT GENERATION (9 LINES)
    d_processes = ['D1 - Classifier Sent', 'D2 - Analysis Sent', 'D3 - Testing Report Sent']
    plot_df = full_df[full_df['process'].isin(d_processes)]

    if plot_df.empty:
        print("\nNo 'D' processes found for plotting.")
        return

    plt.figure(figsize=(12, 7))
    
    # Define styles to distinguish between D1, D2, and D3
    line_styles = {
        'D1 - Classifier Sent': '-', 
        'D2 - Analysis Sent': '--', 
        'D3 - Testing Report Sent': '-.'
    }
    # Define colors for sublayers
    colors = {1: 'blue', 2: 'green', 3: 'red'}

    for proc in d_processes:
        for sub in sorted(plot_df['sublayers'].unique()):
            subset = plot_df[(plot_df['process'] == proc) & (plot_df['sublayers'] == sub)]
            subset = subset.sort_values('neurons')
            
            if not subset.empty:
                label = f"{proc} (Sublayers {sub})"
                plt.plot(subset['neurons'], subset['avg_latency'], 
                         label=label, 
                         color=colors[sub], 
                         linestyle=line_styles[proc], 
                         marker='o')

    plt.title('Latency vs Neurons per Path D Process and Sublayers')
    plt.xlabel('Number of Neurons')
    plt.ylabel('Avg Latency (s)')
    plt.xticks([32, 64, 128, 256])
    plt.grid(True, which='both', linestyle='--', alpha=0.5)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')
    plt.tight_layout()
    
    plt.savefig('latency_path_d_9_lines.png')
    print(f"\nPlot with 9 lines saved as 'latency_path_d_9_lines.png'")
    plt.show()

if __name__ == "__main__":
    aggregate_data()