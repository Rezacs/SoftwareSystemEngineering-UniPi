"""
    PlayerStoreController module, for label storing,
    and prompting report generation
"""
import threading
import pandas as pd
import sqlite3
import os

from src.eval_ambient_flags_loader import DEBUGGING
from src.player_store import PlayerStore
from src.evaluation_report_controller import EvaluationReportController
from src.utility import data_folder

def prepare_label_dict(player_id, rating, source):
    """
    Generate a Label object as dictionary
    """
    return {
        'player_id': player_id,
        'rating': rating,
        'source': source
    }

class PlayerStoreController:
    """
        Class for managing Label storage calls,
        and clearing the buffer after reports are generated.
    """
    def __init__(self):
        self.store = PlayerStore()
        self.report = EvaluationReportController()
        
        # Thread lock to prevent database crashes if multiple payloads arrive simultaneously
        self.db_semaphore = threading.Semaphore()
        
        # Build the exact path to the database
        self.db_path = os.path.join(data_folder, "evaluationDB.db")

    def save_label_prompt_eval(self, label_dict, eval_config=None):
        """
        Stores the incoming label into the correct SQLite table.
        (Batch counting and report triggering is now handled by the Orchestrator)
        """
        label_source = label_dict['source']
        label_df = pd.DataFrame([label_dict])

        # Lock the thread before writing to SQLite
        self.db_semaphore.acquire()

        try:
            if label_source == "expert":
                self.store.ps_store_label_df(label_df, "expertLabelTable")
                if DEBUGGING:
                    print(f"[{label_dict['player_id']}] Saved to Expert buffer.")
                    
            elif label_source == "classifier":
                self.store.ps_store_label_df(label_df, "classifierLabelTable")
                if DEBUGGING:
                    print(f"[{label_dict['player_id']}] Saved to Classifier buffer.")

        except Exception as e:
            print(f"Error saving label in PlayerStoreController: {e}")
        finally:
            # Always release the lock so the system doesn't freeze
            self.db_semaphore.release()

    def remove_labels(self, player_id=None):
        """
        BPMN Task: REMOVE LABELS
        Updated for Batch Processing: Clears the entire database buffer 
        now that the batch evaluation report has been generated.
        """
        self.db_semaphore.acquire()
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear the entire batch from both tables
            cursor.execute("DELETE FROM expertLabelTable")
            cursor.execute("DELETE FROM classifierLabelTable")
            
            conn.commit()
            conn.close()
            print("Buffer Cleared: All labels for the current batch successfully removed.")
            
        except Exception as e:
            print(f"Error clearing batch labels from database: {e}")
        finally:
            self.db_semaphore.release()