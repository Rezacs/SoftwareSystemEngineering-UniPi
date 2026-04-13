import sqlite3
import threading


class SQLiteStore:
    """
    Handles SQLite operations for evaluation system
    """

    def __init__(self, db_path):
        self.db_path = db_path
        self._local = threading.local()
        self._init_db()

    @property
    def conn(self):
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(self.db_path)
        return self._local.conn

    def _init_db(self):
        cur = self.conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS expert_labels (
            player_id TEXT PRIMARY KEY,
            label REAL
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS classifier_labels (
            player_id TEXT PRIMARY KEY,
            label REAL
        )
        """)

        self.conn.commit()

    # ================= INSERT =================

    def insert(self, player_id, label, source):
        table = "expert_labels" if source == "expert" else "classifier_labels"

        self.conn.execute(
            f"INSERT OR REPLACE INTO {table} VALUES (?, ?)",
            (player_id, label)
        )
        self.conn.commit()

    # ================= MATCHING =================

    def fetch_matched(self):
        cur = self.conn.cursor()

        cur.execute("""
        SELECT e.player_id, e.label, c.label
        FROM expert_labels e
        INNER JOIN classifier_labels c
        ON e.player_id = c.player_id
        """)

        return cur.fetchall() or []

    def count_matched(self):
        cur = self.conn.cursor()

        cur.execute("""
        SELECT COUNT(*)
        FROM expert_labels e
        INNER JOIN classifier_labels c
        ON e.player_id = c.player_id
        """)

        row = cur.fetchone()
        return row[0] if row else 0

    # ================= FOR DEBUG (OPTIONAL) =================

    def fetch_all_raw(self):
        expert = list(self.conn.execute("SELECT * FROM expert_labels"))
        classifier = list(self.conn.execute("SELECT * FROM classifier_labels"))
        return expert, classifier

    # ================= CLEAN =================

    def clear(self):
        self.conn.execute("DELETE FROM expert_labels")
        self.conn.execute("DELETE FROM classifier_labels")
        self.conn.commit()

    def delete(self, player_id):
        self.conn.execute("DELETE FROM expert_labels WHERE player_id = ?", (player_id,))
        self.conn.execute("DELETE FROM classifier_labels WHERE player_id = ?", (player_id,))
        self.conn.commit()