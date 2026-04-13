import sqlite3
import pandas as pd
from pathlib import Path
import threading

class RecordsBuffer:

    def __init__(self, db_path: str = "fscDB.db"):
        """
        :param db_path: path where the sqlite3 will be created
        """
        database_path = Path(db_path)
        if database_path.exists():
            database_path.unlink()

        self.__database_path = database_path
        
        # [MODIFICATION 2: Created thread-local storage locker]
        self.thread_data = threading.local()

    # [MODIFICATION 3: Created a property to dynamically serve the correct connection]
    @property
    def db_connection(self):
        """
        Whenever self.db_connection is called, this checks if the CURRENT thread 
        has a connection. If not, it safely creates one. 
        """
        if not hasattr(self.thread_data, 'conn'):
            #thread-safe.
            self.thread_data.conn = sqlite3.connect(str(self.__database_path), timeout=15)
        return self.thread_data.conn

    def __del__(self):
        # [MODIFICATION 4: Updated to safely check the thread-local storage]
        if hasattr(self, 'thread_data') and hasattr(self.thread_data, 'conn'):
            self.thread_data.conn.close()

    def __execute_commit_query(self, query: str, params: list):
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
        if "CREATE TABLE" not in query:
            return False
        return self.__execute_commit_query(query, params)

    def update(self, query: str, params: list) -> bool:
        if "UPDATE" not in query:
            return False
        return self.__execute_commit_query(query, params)

    def delete(self, query: str, params: list) -> bool:
        if "DELETE" not in query:
            return False
        return self.__execute_commit_query(query, params)
    
    def upsert_with_dataframe(self, dataframe: pd.DataFrame) -> bool:
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

    def insert_dataframe(self, dataframe: pd.DataFrame, sample_type: str) -> bool:
        try:
            # [MODIFICATION 5: Removed manual sqlite3.connect, using property instead]
            res = dataframe.to_sql("records", self.db_connection, if_exists="append", index=False)
        except sqlite3.Error as er:
            print(er.sqlite_errorcode) 
            print(er.sqlite_errorname) 
            return False
        return bool(res)

    def read_sql(self, query: str, params=None):
        if params is None:
            params = []  
        return pd.read_sql(query, self.db_connection, params=params)

    def drop_table(self, table: str) -> bool:
        return self.__execute_commit_query("DROP TABLE IF EXISTS ?;", [table])

    def drop_database(self) -> None:
        try:
            self.__database_path.unlink()
        except FileNotFoundError:
            return
    
    def init_db(self):
        # [MODIFICATION 6]
        # The db_connection property handles connection creation automatically now.
        
        table = """CREATE TABLE IF NOT EXISTS records 
                (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER UNIQUE,
                skill_overall INTEGER DEFAULT -1,
                number_of_likes INTEGER DEFAULT -1,
                number_of_followers INTEGER DEFAULT -1,
                days_missed INTEGER DEFAULT -1,
                games_missed INTEGER DEFAULT -1,
                label INTEGER DEFAULT -1
                );"""
        
        if self.create_table(table, []):
            print("table correctly created")
            return True
        else:
            print("error encountered creating records table")
            return False
    
    def shutdown_DB(self):
        # [MODIFICATION 7: Safely close the thread's connection]
        if hasattr(self.thread_data, 'conn'):
            self.thread_data.conn.close()
       
    def deleteRecord(self, id: int):
        query = "DELETE FROM records WHERE ID = ?"
        self.__execute_commit_query(query, [id])

    def retrieveRecord(self, id: int):
        query = "SELECT * FROM records WHERE ID = ?"
        self.read_sql(query, [id])

    def getNumberOfAvailableRecords(self):
        query = "SELECT COUNT(*) FROM RECORDS WHERE label <> -1"
        cursor = self.db_connection.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        count = result[0]
        return count

    def retrieve_last_records(self) -> pd.DataFrame:
        select_query = "SELECT * FROM records WHERE label <> -1"
        df = pd.read_sql(select_query, self.db_connection)
    
        if df.empty:
            return df

        fetched_ids = df['ID'].tolist()
        return df, fetched_ids
        
    def delete_records(self, ids: list) -> bool:
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