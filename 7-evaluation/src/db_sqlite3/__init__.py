"""
This module offers classes to set up and deploy a sqlite3 database.
"""

import os
import sqlite3
import pandas as pd

class DatabaseController:
    """
    Class that covers all low-level accesses to the database.
    This class does not implement any sanity check on queries.
    """

    def __init__(self, db_path: str):
        """
        :param db_path: path where the sqlite3 will be created.
        """
        self.__database_path = db_path
        # FIX: Actually establish the connection so self.conn exists!
        try:
            self.conn = sqlite3.connect(self.__database_path, timeout=15)
            print(f"Database connection established: {self.__database_path}")
        except Exception as e:
            print(f"Error connecting to database: {e}")
            self.conn = None

    def __execute_commit_query(self, query, params=None):
        if self.conn is None:
            print("Database Error: Connection is not established.")
            return False
            
        try:
            cursor = self.conn.cursor()
            
            # FIX: Safely handle queries with and without parameters
            if params is None or len(params) == 0:
                cursor.execute(query)
            else:
                cursor.execute(query, params)
                
            self.conn.commit()
            return True
            
        except Exception as er:
            print(f"Database Error: {er}")
            return False
        
    def create_table(self, query: str, params=None) -> bool:
        """
        Executes query of table creation.
        """
        if "CREATE TABLE" not in query:
            return False
        return self.__execute_commit_query(query, params)

    def update(self, query: str, params=None) -> bool:
        """
        Executes query of table update.
        """
        if "UPDATE" not in query:
            return False
        return self.__execute_commit_query(query, params)

    def delete(self, query: str, params=None) -> bool:
        """
        Executes query of table delete.
        """
        if "DELETE" not in query:
            return False
        return self.__execute_commit_query(query, params)

    def insert_dataframe(self, dataframe: pd.DataFrame, table: str) -> bool:
        """
        Insert dataframe into table using pandas.
        """
        try:
            # We use a context manager here to ensure connection closure for pandas
            with sqlite3.connect(self.__database_path, timeout=15) as db_connection:
                res = dataframe.to_sql(table, db_connection, if_exists="append", index=False)
                return True
        except Exception as er:
            print(f"Pandas SQL Error: {er}")
            return False

    def read_sql(self, query: str, params=None):
        """
        Reads table or result of query from db using pandas.
        """
        try:
            with sqlite3.connect(self.__database_path, timeout=15) as db_connection:
                return pd.read_sql(query, db_connection, params=params if params else [])
        except Exception as er:
            print(f"Read SQL Error: {er}")
            return None

    def drop_table(self, table: str) -> bool:
        """
        Drops a table if it exists.
        """
        # SQLite doesn't support parameters for table names in DROP TABLE, 
        # so we format the string safely for internal use.
        query = f"DROP TABLE IF EXISTS {table};"
        return self.__execute_commit_query(query)

    def drop_database(self) -> None:
        """
        Closes connection and removes the DB file.
        """
        try:
            if self.conn:
                self.conn.close()
            if os.path.exists(self.__database_path):
                os.remove(self.__database_path)
                print("Database dropped successfully.")
        except Exception as e:
            print(f"Error dropping database: {e}")