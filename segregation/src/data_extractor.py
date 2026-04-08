"""Reads labels, features, and active prepared sessions from the local segregation SQLite database."""

import sqlite3


class DataExtractor:
    def _connect(self, db_path: str):
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def extract_grouped_labels(self, db_path: str) -> dict:
        with self._connect(db_path) as connection:
            rows = connection.execute(
                """
                SELECT label, COUNT(*) AS num_samples
                FROM prepared_sessions
                WHERE to_process = 1
                GROUP BY label
                """
            ).fetchall()

        return {
            row["label"]: row["num_samples"]
            for row in rows
            if row["label"] is not None
        }

    def extract_labels(self, db_path: str) -> list[int]:
        with self._connect(db_path) as connection:
            rows = connection.execute(
                """
                SELECT label
                FROM prepared_sessions
                WHERE to_process = 1
                ORDER BY id
                """
            ).fetchall()

        return [row["label"] for row in rows if row["label"] is not None]

    def extract_features(self, db_path: str) -> dict:
        feature_map = {
            "skill_overall": [],
            "social_influence_score": [],
            "injuries_impact_score": [],
        }

        with self._connect(db_path) as connection:
            rows = connection.execute(
                """
                SELECT skill_overall, social_influence_score, injuries_impact_score
                FROM prepared_sessions
                WHERE to_process = 1
                ORDER BY id
                """
            ).fetchall()

        for row in rows:
            feature_map["skill_overall"].append(row["skill_overall"])
            feature_map["social_influence_score"].append(row["social_influence_score"])
            feature_map["injuries_impact_score"].append(row["injuries_impact_score"])

        return feature_map

    def extract_all(self, db_path: str) -> list[dict]:
        with self._connect(db_path) as connection:
            rows = connection.execute(
                """
                SELECT session_id, player_id, label,
                       skill_overall, social_influence_score, injuries_impact_score
                FROM prepared_sessions
                WHERE to_process = 1
                ORDER BY id
                """
            ).fetchall()

        return [
            {
                "session_id": row["session_id"],
                "player_id": row["player_id"],
                "label": row["label"],
                "skill_overall": row["skill_overall"],
                "social_influence_score": row["social_influence_score"],
                "injuries_impact_score": row["injuries_impact_score"],
            }
            for row in rows
        ]
