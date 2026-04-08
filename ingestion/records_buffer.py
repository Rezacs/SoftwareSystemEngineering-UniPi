import os
import sqlite3
import pandas as pd
from ingestion.raw_session_creator import RawSessionCreator

"""
    sqlite3 Error : sqlite_[errorcode/errorname] require sqlite3 version 3.11
    https://docs.python.org/3/library/sqlite3.html#sqlite3.Error.sqlite_errorcode
"""    


class RecordsBuffer:

    def __init__(self,db_path: str = "fscDB.db"):
        """
        :param db_path: path where the sqlite3 will be created,
            Use value ":memory:" to create an SQLite database existing only in memory .
            Give a <pathLike> object, i.e. str or bytes. test
            Can use os.fspath(path) when passing this parameter.
        """

        if os.path.exists(db_path):
            os.remove(db_path)

        self.__database_path = db_path

    def __del__(self):
        if hasattr(self, 'db_connection') and self.db_connection:
            self.db_connection.close()

    def __execute_commit_query(self, query: str, params: list):
        """
        :param query: single SQL statement
        :param params: Python values to bind to placeholders in sql.
            A sequence if unnamed placeholders are used.
            See https://docs.python.org/3/library/sqlite3.html#sqlite3-placeholders .
        :return: False if any error occurs, else True.
        """
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(query, params)
            self.db_connection.commit()
            return True
        except sqlite3.Error as er:
            print(f"Error {er.sqlite_errorcode}: {er.sqlite_errorname}")
            # 2. CRITICAL: Roll back the failed transaction so the connection isn't poisoned!
            self.db_connection.rollback()
            return False

    def create_table(self, query: str, params: list) -> bool:
        """
        Executes query of table creation, with given parameters if any
        :return: False if any error occurs, else True.
        """
        if "CREATE TABLE" not in query:
            return False
        return self.__execute_commit_query(query, params)

    def update(self, query: str, params: list) -> bool:
        """
        Executes query of table update, with given parameters if any.
        :return: False if any error occurs, else True.
        """
        if "UPDATE" not in query:
            return False
        return self.__execute_commit_query(query, params)

    def delete(self, query: str, params: list) -> bool:
        """
        Executes query of table delete, with given parameters if any.
        :return: False if any error occurs, else True.
        """
        if "DELETE" not in query:
            return False
        return self.__execute_commit_query(query, params)
    
    def upsert_with_dataframe(self,dataframe: pd.DataFrame) -> bool:
        if 'player_id' not in dataframe.columns:
            print("Error: DataFrame must contain 'player_id'.")
            return False

        try:
            cursor = self.db_connection.cursor()

            # 1. Dynamically build the column names and placeholders
            columns = list(dataframe.columns)
            cols_string = ", ".join(columns)
        
            # Creates a string like "?, ?, ?" depending on how many columns you have
            placeholders = ", ".join(["?" for _ in columns]) 
        
            # 2. Build the UPDATE clause (excluding playerID)
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

            # 3. Convert DataFrame to a list of tuples for executemany
            # itertuples is the fastest way to extract rows from Pandas to Python tuples
            data_tuples = list(dataframe.itertuples(index=False, name=None))

            # 4. Execute the raw SQL directly
            cursor.executemany(upsert_sql, data_tuples)
            self.db_connection.commit()

            """
            #PRINT CODE
            
            print("\n--- Current State of 'records' Table ---")
            
            # Read the whole table into a new DataFrame for pretty printing
            current_table = pd.read_sql("SELECT * FROM records", self.db_connection)
            
            # .to_string() forces Pandas to print all columns and rows without truncating
            print(current_table.to_string()) 
            print("----------------------------------------\n")

            """

            return True

        except sqlite3.Error as er:
            print(f"SQLite Error: {er.sqlite_errorcode} - {er.sqlite_errorname}")
            print(f"Detailed Message: {er}") 
            self.db_connection.rollback()
            self.db_connection.rollback()
            return False

    def insert_dataframe(self, dataframe: pd.DataFrame, sample_type: str) -> bool:
        """
        Insert dataframe into table using pandas.DataFrame.to_sql,
            see : https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html .
        :param dataframe: dataframe that is has to be uploaded in target db.
        :param sample_type: type of sample received in order to fill the correct columns
        :return: True if any row was affected, False otherwise.
        """
        try:
            db_connection = sqlite3.connect(self.__database_path, timeout=15)
            res = dataframe.to_sql("records", db_connection, if_exists="append", index=False)
        except sqlite3.Error as er:
            print(er.sqlite_errorcode)  # Prints 275
            print(er.sqlite_errorname)  # Prints SQLITE_CONSTRAINT_CHECK
            return False
        return bool(res)

    def read_sql(self, query: str, params=None):
        """
        Reads table or result of query from db using pandas.read_sql,
            see : https://pandas.pydata.org/docs/reference/api/pandas.read_sql.html .
        :param query: str SQL query to be executed, or a table name.
        :param params: Parameters to bind to the query (default is None).
        :return: DataFrame or Iterator[DataFrame].
        """
        if params is None:
            params = []  # Default is an empty list if no parameters are provided
        return pd.read_sql(query,self.db_connection,params=params)

    def drop_table(self, table: str) -> bool:
        """
        :param table: str name of Table to drop_if_exists from db.
        :return: False if any error occurs, else True.
        """
        return self.__execute_commit_query("DROP TABLE IF EXISTS ?;", [table])

    def drop_database(self) -> None:
        """
        Drop database (knows its location since __init__).
        :return:
        """
        try:
            os.remove(self.__database_path)
        except FileNotFoundError:
            return
    
    def init_db(self):
               
        self.db_connection = sqlite3.connect(self.__database_path, timeout=15, check_same_thread=False)
        # Creation of the records table
        table = """CREATE TABLE IF NOT EXISTS records 
                (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER UNIQUE,
                skill_overall FLOAT DEFAULT -1.0,
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
        if self.db_connection:
            self.db_connection.close()
       
    def deleteRecord(self,id : int):
        query = "DELETE FROM records WHERE ID = ?"
        self.__execute_commit_query(query,[id])

    def retrieveRecord(self,id : int):
        query = "SELECT * FROM records WHERE ID = ?"
        self.read_sql(query,[id])

    def getNumberOfAvailableRecords(self):
        query = "SELECT COUNT(*) FROM RECORDS"
        cursor=self.db_connection.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        count = result[0]
        return count

    def retrieve_last_records(self, rows_to_fetch: int) -> pd.DataFrame:
        # 1. Fetch records using ORDER BY, starting from the older ones to to newest one
        # (Assuming you have an 'id' or 'created_at' column to define order)
        select_query = "SELECT * FROM records ORDER BY ID ASC LIMIT ?"
    
        # Read into DataFrame
        df = pd.read_sql(
            select_query, 
            self.db_connection, 
            params=[rows_to_fetch]
        )
    
        # 2. If no records were fetched, return early
        if df.empty:
            return df

        print(df)

        fetched_ids = df['ID'].tolist()
    
        return df,fetched_ids
        

    def delete_records(self, ids: list) -> bool:
        # Safely delete ONLY the records fetched by their IDs
    
        # 1. Early exit if the list is empty (prevents SQL syntax errors)
        if not ids:
            print("No IDs provided for deletion.")
            return False

        try:
            # Create placeholders for the IN clause (e.g., "?, ?, ?")
            placeholders = ",".join(["?"] * len(ids))
            delete_query = f"DELETE FROM records WHERE ID IN ({placeholders})"
    
            # Execute the deletion and commit
            cursor = self.db_connection.cursor()
            cursor.execute(delete_query, ids)
            self.db_connection.commit()

            """

            print("\n--- Current State of 'records' Table ---")
        
            # Read the whole table into a new DataFrame for pretty printing
            current_table = pd.read_sql("SELECT * FROM records", self.db_connection)
        
            # .to_string() forces Pandas to print all columns and rows without truncating
            print(current_table.to_string()) 
            print("----------------------------------------\n")

            """
        
            return True

        except Exception as e:
            # 2. Catch the error, optionally rollback, and return False
            print(f"[ERROR] Failed to delete records: {e}")
        
            # Good practice: Rollback the transaction if an error occurred to avoid database locks
            try:
                self.db_connection.rollback()
            except Exception:
                pass 
            
            return False
    

