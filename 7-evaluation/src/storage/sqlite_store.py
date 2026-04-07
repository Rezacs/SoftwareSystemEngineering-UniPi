import sqlite3


class SQLiteStore:
    """
    Handles SQLite operations for evaluation system
    """

    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        cur = self.conn.cursor()

        # Expert labels
        cur.execute("""
        CREATE TABLE IF NOT EXISTS expert_labels (
            player_id TEXT PRIMARY KEY,
            label REAL
        )
        """)

        # Classifier labels
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

        # REPLACE avoids duplicates (latest value wins)
        self.conn.execute(
            f"INSERT OR REPLACE INTO {table} VALUES (?, ?)",
            (player_id, label)
        )
        self.conn.commit()

    # ================= MATCHING =================

    def fetch_matched(self):
        """
        Returns only matched pairs (INNER JOIN)
        """
        cur = self.conn.cursor()

        cur.execute("""
        SELECT e.player_id, e.label, c.label
        FROM expert_labels e
        INNER JOIN classifier_labels c
        ON e.player_id = c.player_id
        """)

        return cur.fetchall()

    def count_matched(self):
        """
        Count matched pairs (for batch logic)
        """
        cur = self.conn.cursor()

        cur.execute("""
        SELECT COUNT(*)
        FROM expert_labels e
        INNER JOIN classifier_labels c
        ON e.player_id = c.player_id
        """)

        return cur.fetchone()[0]

    # ================= FOR DEBUG (OPTIONAL) =================

    def fetch_all_raw(self):
        """
        Debug only — not used in evaluation
        """
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