"""Manages persistent storage of prepared sessions inside the local segregation SQLite database."""

import sqlite3
from pathlib import Path


class SessionRepository:
    def initialize(self, db_path: str):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS prepared_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    player_id INTEGER NOT NULL,
                    label INTEGER,
                    skill_overall REAL NOT NULL,
                    social_influence_score REAL NOT NULL,
                    injuries_impact_score REAL NOT NULL,
                    to_process INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            connection.commit()

    def store(self, prepared_session: dict, db_path: str, to_process: bool = True):
        with sqlite3.connect(db_path) as connection:
            connection.execute(
                """
                INSERT INTO prepared_sessions (
                    session_id,
                    player_id,
                    label,
                    skill_overall,
                    social_influence_score,
                    injuries_impact_score,
                    to_process
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prepared_session.get("session_id"),
                    prepared_session.get("player_id"),
                    prepared_session.get("label"),
                    float(prepared_session.get("skill_overall", 0) or 0),
                    float(prepared_session.get("social_influence_score", 0) or 0),
                    float(prepared_session.get("injuries_impact_score", 0) or 0),
                    1 if to_process else 0,
                ),
            )
            connection.commit()

    def receive(self, db_path: str, to_process_only: bool = True):
        query = """
            SELECT session_id, player_id, label,
                   skill_overall, social_influence_score, injuries_impact_score
            FROM prepared_sessions
        """
        if to_process_only:
            query += " WHERE to_process = 1"
        query += " ORDER BY id"

        with sqlite3.connect(db_path) as connection:
            rows = connection.execute(query).fetchall()

        return [
            {
                "session_id": row[0],
                "player_id": row[1],
                "label": row[2],
                "skill_overall": row[3],
                "social_influence_score": row[4],
                "injuries_impact_score": row[5],
            }
            for row in rows
        ]

    def sessions_count(self, db_path: str, to_process_only: bool = True) -> int:
        query = "SELECT COUNT(*) FROM prepared_sessions"
        if to_process_only:
            query += " WHERE to_process = 1"

        with sqlite3.connect(db_path) as connection:
            return int(connection.execute(query).fetchone()[0])

    def receiveStored(self, db_path: str):
        return self.receive(db_path, to_process_only=False)

    def mark_all_to_process(self, db_path: str):
        with sqlite3.connect(db_path) as connection:
            connection.execute("UPDATE prepared_sessions SET to_process = 1")
            connection.commit()

    def promote_pending_sessions(self, db_path: str):
        with sqlite3.connect(db_path) as connection:
            connection.execute("UPDATE prepared_sessions SET to_process = 1 WHERE to_process = 0")
            connection.commit()

    def delete_processed_sessions(self, db_path: str):
        with sqlite3.connect(db_path) as connection:
            connection.execute("DELETE FROM prepared_sessions WHERE to_process = 1")
            connection.commit()
