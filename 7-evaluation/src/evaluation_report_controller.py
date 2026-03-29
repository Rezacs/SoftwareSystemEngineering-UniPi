import sqlite3
import pandas as pd
import os
from datetime import datetime
from src.utility import data_folder

class EvaluationReportController:
    def __init__(self):
        self.db_path = os.path.join(data_folder, "evaluationDB.db")
        self.report_folder = os.path.join(data_folder, "reports")
        
        # Ensure a 'reports' folder exists to store the output
        if not os.path.exists(self.report_folder):
            os.makedirs(self.report_folder)

    def generate_human_report(self, player_id):
        """
        Creates a readable text report for the human evaluator.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            df_c = pd.read_sql("SELECT rating, source FROM classifierLabelTable WHERE player_id = ?", conn, params=[player_id])
            df_e = pd.read_sql("SELECT rating, source FROM expertLabelTable WHERE player_id = ?", conn, params=[player_id])
            conn.close()

            if df_c.empty or df_e.empty:
                return # Not enough data for a comparison yet

            ai_val = df_c['rating'].iloc[-1]
            human_val = df_e['rating'].iloc[-1]
            diff = abs(ai_val - human_val)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Create a professional looking report string
            report_content = f"""
====================================================
FOOTBALL SOCIAL CLUB - EVALUATION AUDIT REPORT
====================================================
Generated on: {timestamp}
Target Player: {player_id}
----------------------------------------------------
RATINGS SUMMARY:
- AI Classifier Rating:  {ai_val} / 5
- Human Expert Rating:   {human_val} / 5
----------------------------------------------------
ANALYSIS:
Discrepancy Score: {diff}
Status: {"CONSISTENT" if diff <= 1 else "REQUIRES MANUAL REVIEW"}

NOTES FOR EVALUATOR:
{ "The AI and Expert are in alignment. High confidence in data." if diff <= 1 else 
  "CRITICAL: Large gap between AI and Human perception. Please review match footage."}
====================================================
"""
            # Save to a file
            report_filename = f"Report_{player_id}.txt"
            report_path = os.path.join(self.report_folder, report_filename)
            
            with open(report_path, "w") as f:
                f.write(report_content)
            
            print(f"--- Human-Readable Report generated: {report_filename} ---")

        except Exception as e:
            print(f"Failed to generate human report: {e}")