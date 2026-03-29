"""
    Module for interaction with player labels' DataBase (creation, push/pop)
"""
import logging
import os
from src.db_sqlite3 import DatabaseController

from src.eval_ambient_flags_loader import DELETE_DB_ON_LOAD, DB_NAME

class PlayerStore:
    """
    Class for general interaction with player label DB
    """

    def __init__(self):
        if DELETE_DB_ON_LOAD:
            if os.path.exists(DB_NAME):
                os.remove(DB_NAME)
            print(f'flag is set to DELETE_DB_ON_LOAD with name : {DB_NAME}')
        self.db = DatabaseController(DB_NAME)

    def ps_store_label_df(self, label, table):
        """
        Insert label_dataframe object into target table of DataBase
        """
        if not self.db.insert_dataframe(label, table):
            logging.error("Impossible to <insert_dataframe>, in table : {%s}", table)
            raise ValueError("Evaluation System label storage failed")

    def ps_create_table(self, query, params=None):
        """
        Create a table safely using db_sqlite3
        """
        if not self.db.create_table(query, params):
            logging.error("Impossible to <create> the table with query : {%s}", query)
            raise ValueError("Evaluation System create_table failed")

    def ps_delete_labels(self, query, params=None):
        """
        Delete rows using db_sqlite3
        """
        if not self.db.delete(query, params):
            logging.error("Impossible to <delete> with query : {%s}", query)
            raise ValueError("Evaluation System delete_labels failed")

    def ps_select_labels(self, query, params=None):
        """
        Fetch data back as a Pandas DataFrame
        """
        return self.db.read_sql(query, params)