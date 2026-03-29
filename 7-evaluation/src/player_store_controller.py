"""
    PlayerStoreController module, for label storing,
    and prompting report generation
"""
import threading
import pandas as pd

from src.eval_ambient_flags_loader import DEBUGGING
from src.player_store import PlayerStore
from src.evaluation_report_controller import EvaluationReportController

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
        and requiring EvaluationReport generation if conditions are met.
    """
    def __init__(self):
        self.num_labels_from_expert = 0
        self.num_labels_from_classifier = 0
        self.enough_total_labels = False
        
        self.store = PlayerStore()
        self.report = EvaluationReportController()
        self.db_semaphore = threading.Semaphore()

    def save_label_prompt_eval(self, label_dict, eval_config):
        """
        Check batch limits, store label, trigger evaluation if ready.
        """
        min_labels = eval_config['min_labels_opinionated']
        max_conflict = eval_config['max_conflicting_labels_threshold']
        max_cons_conflict = eval_config['max_consecutive_conflicting_labels_threshold']

        label_source = label_dict['source']
        label_df = pd.DataFrame([label_dict])

        # Lock the thread to prevent database crashes if payloads arrive simultaneously
        self.db_semaphore.acquire()

        try:
            if label_source == "expert":
                self.store.ps_store_label_df(label_df, "expertLabelTable")
                self.num_labels_from_expert += 1
            elif label_source == "classifier":
                self.store.ps_store_label_df(label_df, "classifierLabelTable")
                self.num_labels_from_classifier += 1

            if DEBUGGING:
                print(f"Expert: {self.num_labels_from_expert} | Classifier: {self.num_labels_from_classifier}")

            if self.num_labels_from_expert >= min_labels and self.num_labels_from_classifier >= min_labels:
                self.enough_total_labels = True

            if self.enough_total_labels:
                expert_df = self.store.ps_select_labels("SELECT * FROM expertLabelTable")
                classifier_df = self.store.ps_select_labels("SELECT * FROM classifierLabelTable")

                # Find players evaluated by BOTH the expert and the classifier
                common_ids = set(expert_df['player_id']).intersection(set(classifier_df['player_id']))

                if len(common_ids) >= min_labels:
                    opinionated_player_id_list = list(common_ids)[:min_labels]
                    
                    matched_expert = expert_df[expert_df['player_id'].isin(opinionated_player_id_list)]
                    matched_classifier = classifier_df[classifier_df['player_id'].isin(opinionated_player_id_list)]

                    opinionated_labels = {
                        "expert": matched_expert,
                        "classifier": matched_classifier
                    }

                    # Delete only the labels we just used to keep the DB clean
                    id_tuple_string = str(opinionated_player_id_list)[1:-1]
                    self.store.ps_delete_labels(f"DELETE FROM expertLabelTable WHERE player_id IN ({id_tuple_string})")
                    self.store.ps_delete_labels(f"DELETE FROM classifierLabelTable WHERE player_id IN ({id_tuple_string})")

                    self.num_labels_from_expert -= min_labels
                    self.num_labels_from_classifier -= min_labels
                    self.enough_total_labels = False

                    self.db_semaphore.release()

                    # Trigger report generation in the background!
                    print("Start EvaluationReport generation")
                    thread = threading.Thread(target=self.report.generate_report,
                                              args=(min_labels, max_conflict, max_cons_conflict, opinionated_labels))
                    thread.start()
                    return

        except Exception as e:
            print(f"Error in PlayerStoreController: {e}")
        finally:
            if self.db_semaphore._value == 0:
                self.db_semaphore.release()

    def remove_labels(self, player_id):
        """
        Removes the player's labels from the buffer 
        after the evaluation report is generated.
        """
        import sqlite3
        import os
        from src.utility import data_folder

        # Build the exact path to the database manually
        db_path = os.path.join(data_folder, "evaluationDB.db")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Delete the specific player's data from both tables
            cursor.execute("DELETE FROM expertLabelTable WHERE player_id = ?", (player_id,))
            cursor.execute("DELETE FROM classifierLabelTable WHERE player_id = ?", (player_id,))
            
            conn.commit()
            conn.close()
            
            print(f"Buffer Cleared: Labels for {player_id} successfully removed from database.")
            
        except Exception as e:
            print(f"Error removing labels for {player_id}: {e}")