import sqlite3
import threading
from pathlib import Path

import pandas as pd


class RecordsBuffer:
    """Manages the connection with the SQL database buffer to insert and extract records.

    This class provides a thread-safe interface for SQLite database operations,
    allowing multiple threads to interact with the database without locking conflicts.

    Attributes:
        __database_path (Path): The file path to the SQLite database.
        thread_data (threading.local): Thread-local storage used to handle distinct
            database connections for different active threads.
    """

    def __init__(self, db_path: str = "fscDB.db"):
        """Initializes the record buffer and sets up the database file.

        If a database file already exists at the specified path, it is deleted
        to ensure a fresh start.

        Args:
            db_path (str, optional): The file path where the SQLite database
                will be created. Defaults to "fscDB.db".
        """
        database_path = Path(db_path)
        if database_path.exists():
            database_path.unlink()

        self.__database_path = database_path
        # Created thread-local storage locker
        self.thread_data = threading.local()

    @property
    def db_connection(self):
        """Dynamically serves a thread-safe connection to the database.

        Whenever this property is called, it checks if the CURRENT thread
        has an active connection. If not, it safely creates one.

        Returns:
            sqlite3.Connection: A thread-safe connection object to the database.
        """
        if not hasattr(self.thread_data, 'conn'):
            # thread-safe.
            self.thread_data.conn = sqlite3.connect(str(self.__database_path), timeout=15)
        return self.thread_data.conn

    def __del__(self):
        """Safely closes the thread-local database connection upon object destruction."""
        # Updated to safely check the thread-local storage
        if hasattr(self, 'thread_data') and hasattr(self.thread_data, 'conn'):
            self.thread_data.conn.close()

    def __execute_commit_query(self, query: str, params: list):
        """Executes a query that modifies the database and commits the transaction.

        Args:
            query (str): The SQL query to execute.
            params (list): A list of parameters to bind to the query.

        Returns:
            bool: True if the query executed and committed successfully, False otherwise.
        """
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(query, params)
            self.db_connection.commit()
            return True
        except sqlite3.Error as er:
            print(f"Error {er.sqlite_errorcode}: {er.sqlite_errorname}")
            self.db_connection.rollback()
            return False

    def create_table(self, query: str, params: list) -> bool:
        """Executes a CREATE TABLE statement in the database.

        Args:
            query (str): The SQL string for creating the table.
            params (list): Parameters to bind to the creation query.

        Returns:
            bool: True if the table was created successfully, False if the
                query is invalid or execution fails.
        """
        if "CREATE TABLE" not in query:
            return False
        return self.__execute_commit_query(query, params)

    def update(self, query: str, params: list) -> bool:
        """Executes an UPDATE statement in the database.

        Args:
            query (str): The SQL string for updating records.
            params (list): Parameters to bind to the update query.

        Returns:
            bool: True if the update was successful, False if the query
                is invalid or execution fails.
        """
        if "UPDATE" not in query:
            return False
        return self.__execute_commit_query(query, params)

    def delete(self, query: str, params: list) -> bool:
        """Executes a DELETE statement in the database.

        Args:
            query (str): The SQL string for deleting records.
            params (list): Parameters to bind to the delete query.

        Returns:
            bool: True if deletion was successful, False if the query
                is invalid or execution fails.
        """
        if "DELETE" not in query:
            return False
        return self.__execute_commit_query(query, params)

    def upsert_with_dataframe(self, dataframe: pd.DataFrame) -> bool:
        """Inserts or updates database records using data from a pandas DataFrame.

        If a 'player_id' already exists in the database, the existing record
        is updated with the new DataFrame values. If it does not exist, a new
        record is inserted.

        Args:
            dataframe (pd.DataFrame): The dataframe containing records to upsert.
                Must contain a 'player_id' column.

        Returns:
            bool: True if the upsert was successful, False if the 'player_id'
                column is missing or a SQLite error occurs.
        """
        if 'player_id' not in dataframe.columns:
            print("Error: DataFrame must contain 'player_id'.")
            return False

        try:
            cursor = self.db_connection.cursor()

            columns = list(dataframe.columns)
            cols_string = ", ".join(columns)
            placeholders = ", ".join(["?" for _ in columns])

            update_cols = [c for c in columns if c != 'player_id']

            if update_cols:
                set_clause = ", ".join([f"{c} = excluded.{c}" for c in update_cols])

                upsert_sql = f"""
                    INSERT INTO records ({cols_string})
                    VALUES ({placeholders})
                    ON CONFLICT(player_id) DO UPDATE SET
                    {set_clause};
                """
            else:
                upsert_sql = f"""
                    INSERT INTO records ({cols_string})
                    VALUES ({placeholders})
                    ON CONFLICT(player_id) DO NOTHING;
                """

            data_tuples = list(dataframe.itertuples(index=False, name=None))

            cursor.executemany(upsert_sql, data_tuples)
            self.db_connection.commit()

            print("\n--- Current State of 'records' Table ---")
            # Read the whole table into a new DataFrame for pretty printing
            current_table = pd.read_sql("SELECT * FROM records", self.db_connection)
            # .to_string() forces Pandas to print all columns and rows without truncating
            print(current_table.to_string())
            print("----------------------------------------\n")

            return True

        except sqlite3.Error as er:
            print(f"SQLite Error: {er.sqlite_errorcode} - {er.sqlite_errorname}")
            print(f"Detailed Message: {er}")
            self.db_connection.rollback()
            return False

    def insert_dataframe(self, dataframe: pd.DataFrame) -> bool:
        """Appends all rows from a pandas DataFrame into the 'records' table.

        Args:
            dataframe (pd.DataFrame): The dataframe containing the rows to insert.

        Returns:
            bool: True if insertion is successful, False if a SQLite error occurs.
        """
        try:
            #Removed manual sqlite3.connect, using property instead
            res = dataframe.to_sql("records", self.db_connection, if_exists="append", index=False)
        except sqlite3.Error as er:
            print(er.sqlite_errorcode)
            print(er.sqlite_errorname)
            return False
        return bool(res)

    def read_sql(self, query: str, params=None):
        """Executes a SQL SELECT query and returns the results as a DataFrame.

        Args:
            query (str): The SELECT query to execute.
            params (list, optional): Parameters to bind to the query. Defaults to None.

        Returns:
            pd.DataFrame: A pandas DataFrame containing the query results.
        """
        if params is None:
            params = []
        return pd.read_sql(query, self.db_connection, params=params)

    def drop_table(self, table: str) -> bool:
        """Drops a specified table from the database if it exists.

        Args:
            table (str): The name of the table to drop.

        Returns:
            bool: True if the table was dropped successfully, False otherwise.
        """
        return self.__execute_commit_query("DROP TABLE IF EXISTS ?;", [table])

    def drop_database(self):
        """Deletes the underlying SQLite database file from the filesystem."""
        try:
            self.__database_path.unlink()
        except FileNotFoundError:
            print(f"ERROR> unable to locate the DB file at : {self.__database_path}")

    def init_db(self):
        """Initializes the database by creating the default 'records' table.

        Returns:
            bool: True if the table was created successfully, False otherwise.
        """
        # The db_connection property handles connection creation automatically now.

        table = """CREATE TABLE IF NOT EXISTS records
                (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER UNIQUE,
                skill_overall INTEGER DEFAULT NULL,
                number_of_likes INTEGER DEFAULT NULL,
                number_of_followers INTEGER DEFAULT NULL,
                days_missed INTEGER DEFAULT NULL,
                games_missed INTEGER DEFAULT NULL,
                label INTEGER DEFAULT NULL
                );"""

        if self.create_table(table, []):
            print("table correctly created")
            return True

        print("ERROR > encountered creating records table")
        return False

    def shutdown_db(self):
        """Closes the database connection for the current active thread."""
        #Safely close the thread's connection
        if hasattr(self.thread_data, 'conn'):
            self.thread_data.conn.close()

    def delete_record(self, record_id: int):
        """Deletes a specific record from the database based on its primary key ID.

        Args:
            record_id (int): The primary key ID of the record to delete.
        """
        query = "DELETE FROM records WHERE ID = ?"
        self.__execute_commit_query(query, [record_id])

    def retrieve_record(self, record_id: int):
        """Retrieves a specific record from the database based on its primary key ID.

        Args:
            id (int): The primary key ID of the record to retrieve.

        Returns:
            pd.DataFrame: A DataFrame containing the requested record.
        """
        query = "SELECT * FROM records WHERE ID = ?"
        return self.read_sql(query, [record_id])

    def get_number_of_available_records(self):
        """Counts the total number of records that have an assigned label.

        Returns:
            int: The total count of labeled records in the database.
        """
        query = "SELECT COUNT(*) FROM RECORDS WHERE label IS NOT NULL"
        cursor = self.db_connection.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        count = result[0]
        return count

    def retrieve_last_records(self):
        """Retrieves all records from the database that have a non-null label.

        Returns:
            pd.DataFrame: If no records are found, returns an empty DataFrame.
            tuple: If records are found, returns a tuple containing (pd.DataFrame
                of records, list of fetched IDs).
        """
        select_query = "SELECT * FROM records WHERE label IS NOT NULL"
        df = pd.read_sql(select_query, self.db_connection)

        if df.empty:
            return df

        fetched_ids = df['ID'].tolist()
        return df, fetched_ids

    def delete_records(self, ids: list) -> bool:
        """Deletes multiple records from the database based on a list of IDs.

        Args:
            ids (list): A list of primary key IDs for the records to delete.

        Returns:
            bool: True if all records were successfully deleted, False if the
                list is empty or an error occurs during execution.
        """
        if not ids:
            print("No IDs provided for deletion.")
            return False

        try:
            placeholders = ",".join(["?"] * len(ids))
            delete_query = f"DELETE FROM records WHERE ID IN ({placeholders})"

            cursor = self.db_connection.cursor()
            cursor.execute(delete_query, ids)
            self.db_connection.commit()
            return True

        except Exception as e:
            print(f"[ERROR] Failed to delete records: {e}")
            try:
                self.db_connection.rollback()
            except Exception:
                pass
            return False
