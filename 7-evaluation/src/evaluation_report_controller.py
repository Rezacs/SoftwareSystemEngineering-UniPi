import os
import json
import sqlite3
from datetime import datetime 
import pandas as pd

# Set Matplotlib to run headlessly (Fixes the thread warning)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.utility import data_folder

class EvaluationReportController:
    def __init__(self):
        # HARDCODED THRESHOLDS (Based on the Mockup's approach)
        self.n_errors_th = 3                 # Max allowed total errors in a batch
        self.max_consecutive_errors_th = 2   # Max allowed consecutive errors
        
        # Define paths
        self.db_path = os.path.join(data_folder, "evaluationDB.db")
        self.report_folder = os.path.join(data_folder, "reports")
        os.makedirs(self.report_folder, exist_ok=True)

    def generate_human_report(self, batch_name, eval_config):
        n_errors_th = eval_config.get("max_conflicting_labels_threshold", 4)
        max_consecutive_errors_th = eval_config.get("max_consecutive_conflicting_labels_threshold", 3)
        rating_tolerance = eval_config.get("rating_tolerance", 0.5)

        try:
            conn = sqlite3.connect(self.db_path)
            
            # MODIFIED: SQL now pulls classifier_id
            query = """
                SELECT e.player_id, e.rating as expert_rating, 
                       c.rating as classifier_rating, c.classifier_id
                FROM expertLabelTable e
                JOIN classifierLabelTable c ON e.player_id = c.player_id
                ORDER BY e.rowid ASC
            """
            df = pd.read_sql_query(query, conn)
            conn.close()

            if df.empty:
                print("Not enough matching labels in the buffer to generate a report.")
                return False

            # Extract the classifier ID (Assume the whole batch uses the same one)
            classifier_id = df['classifier_id'].iloc[0] if 'classifier_id' in df.columns and pd.notna(df['classifier_id'].iloc[0]) else "UNKNOWN_CLASSIFIER"

            # --- 1. CALCULATE METRICS & PREPARE DATAFRAME ---
            total_errors = 0
            consecutive_errors = 0
            max_consecutive_errors = 0
            
            check_data = [] 
            player_details = [] 

            for index, row in df.iterrows():
                expert = float(row['expert_rating'])
                classifier = float(row['classifier_rating'])
                
                diff = abs(expert - classifier)
                is_match = diff <= rating_tolerance
                
                status_text = "MATCH" if is_match else "ERROR"
                check_data.append(status_text)
                
                if is_match:
                    consecutive_errors = 0 
                else:
                    total_errors += 1
                    consecutive_errors += 1
                    if consecutive_errors > max_consecutive_errors:
                        max_consecutive_errors = consecutive_errors
                
                player_details.append({
                    "player_id": row['player_id'],
                    "expert_rating": expert,
                    "classifier_rating": classifier,
                    "difference": round(diff, 2),
                    "status": status_text
                })

            df['CHECK'] = check_data
            is_accepted = bool(total_errors <= n_errors_th and max_consecutive_errors <= max_consecutive_errors_th)

            # --- 2. GENERATE JSON REPORT (With Classifier ID) ---
            report_data = {
                "batch_id": batch_name,
                "classifier_id": classifier_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "system_recommendation": "ACCEPT" if is_accepted else "REJECT",
                "metrics": {
                    "tolerance_used": rating_tolerance,
                    "total_errors": total_errors,
                    "total_errors_threshold": n_errors_th,
                    "max_consecutive_errors": max_consecutive_errors,
                    "max_consecutive_errors_threshold": max_consecutive_errors_th
                },
                "details": player_details
            }

            json_filepath = os.path.join(self.report_folder, f"{batch_name}.json")
            with open(json_filepath, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=4)

            # --- 3. GENERATE STYLED PNG REPORT ---
            png_filepath = os.path.join(self.report_folder, f"{batch_name}.png")
            
            num_rows = len(df)
            plot_height = 5.5 
            table_height = max(3.0, num_rows * 0.45) 
            summary_height = 2.0
            total_height = plot_height + table_height + summary_height

            fig, axs = plt.subplots(3, 1, figsize=(11, total_height), 
                                    gridspec_kw={'height_ratios': [plot_height, table_height, summary_height]})
            
            plt.subplots_adjust(hspace=0.9) 
            
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # MODIFIED: PNG title now shows the Classifier ID
            fig.suptitle(f"Evaluation Report: {batch_name} | Classifier: {classifier_id}\nGenerated: {timestamp_str}\n(Tolerance: ±{rating_tolerance})", fontsize=14, fontweight='bold')
            
            ax_plot = axs[0]
            ax_plot.plot(df['player_id'], df['expert_rating'], marker='o', label='Expert Rating', color='#1f77b4', linewidth=2)
            ax_plot.plot(df['player_id'], df['classifier_rating'], marker='X', linestyle='--', label='Classifier Rating', color='#ff7f0e', linewidth=2)
            
            ax_plot.set_ylabel("Rating (1-5)", fontweight='bold')
            ax_plot.set_xlabel("Player ID", fontweight='bold')
            ax_plot.set_yticks([1, 2, 3, 4, 5])
            ax_plot.set_ylim(0.5, 5.5) 
            
            ax_plot.set_xticks(range(len(df['player_id'])))
            ax_plot.set_xticklabels(df['player_id'], rotation=45, ha='right', fontsize=9)
            ax_plot.tick_params(axis='x', pad=10)
            
            ax_plot.legend(loc='upper right')
            ax_plot.grid(True, linestyle=':', alpha=0.7, axis='y')
            
            ax_table = axs[1]
            ax_table.axis('off') 

            table_data = []
            for _, row in df.iterrows():
                display_check = "✔ MATCH" if row['CHECK'] == "MATCH" else "✘ ERROR"
                table_data.append([row['player_id'], row['expert_rating'], row['classifier_rating'], display_check])
                
            col_labels = ['SESSION/PLAYER ID', 'EXPERT', 'CLASSIFIER', 'CHECK']

            eval_table = ax_table.table(cellText=table_data, colLabels=col_labels, loc='center', cellLoc='center')
            eval_table.auto_set_font_size(False)
            eval_table.set_fontsize(11)
            eval_table.scale(1, 1.8) 

            for (row, col), cell in eval_table.get_celld().items():
                if row == 0:
                    cell.set_facecolor('#4CAF50')
                    cell.set_text_props(weight='bold', color='white')
                else:
                    is_error = "✘ ERROR" in table_data[row-1][3]
                    if is_error:
                        cell.set_facecolor('#ffebee') 
                        if col == 3: 
                            cell.set_text_props(weight='bold', color='#d32f2f')
                    else:
                        cell.set_facecolor('#f1f8e9') 
                        if col == 3:
                            cell.set_text_props(weight='bold', color='#388e3c')

            ax_summary = axs[2]
            ax_summary.axis('off')
            
            summary_color = "green" if is_accepted else "red"
            summary_text = (
                f"N° ERRORS: {total_errors}  (Threshold: {n_errors_th})\n"
                f"MAX CONSECUTIVE ERRORS: {max_consecutive_errors}  (Threshold: {max_consecutive_errors_th})\n\n"
                f"SYSTEM RECOMMENDATION: [{' ✔ ACCEPT ' if is_accepted else ' ✘ REJECT '}]"
            )
            
            ax_summary.text(0.5, 0.5, summary_text, ha='center', va='center', 
                          fontsize=13, fontweight='bold', 
                          bbox=dict(facecolor='white', edgecolor=summary_color, boxstyle='round,pad=1.5', linewidth=2))

            plt.savefig(png_filepath, bbox_inches='tight', pad_inches=0.3, dpi=150)
            plt.close() 

            print(f"--- Reports generated successfully ---")
            print(f"JSON: {json_filepath}")
            print(f"PNG:  {png_filepath}")
            
            return True

        except Exception as e:
            print(f"Error generating report: {e}")
            return False

  