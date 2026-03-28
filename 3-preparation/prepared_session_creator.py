from .utils.feature_extractor import compute_feature_scores


class PreparedSessionCreator:
    def create_prepared_session(self, raw_session: dict) -> dict:
        record = raw_session["records"][0]
        skill_overall, social_influence_score, injuries_impact_score = (
            compute_feature_scores(record)
        )

        return {
            "session_id": raw_session["session_id"],
            "player_id": record["player_id"],
            "label": record.get("label"),
            "features": {
                "skill_overall": round(skill_overall, 2),
                "social_influence_score": round(social_influence_score, 2),
                "injuries_impact_score": round(injuries_impact_score, 2),
            }
        }
