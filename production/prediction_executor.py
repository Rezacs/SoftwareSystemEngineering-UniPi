class PredictionExecutor:
    def predict(self, prepared_session: dict, model: dict) -> dict:
        features = prepared_session.get("features", {})

        skill = float(features.get("skill_overall", 0))
        social = float(features.get("social_influence_score", 0))
        injury = float(features.get("injuries_impact_score", 0))

        raw_score = (0.6 * skill) + (0.3 * social / 1000) - (0.1 * injury / 100)
        raw_score = max(0, min(raw_score, 100))

        if raw_score < 20:
            stars = 1
        elif raw_score < 40:
            stars = 2
        elif raw_score < 60:
            stars = 3
        elif raw_score < 80:
            stars = 4
        else:
            stars = 5

        return {
            "player_id": prepared_session["player_id"],
            "session_id": prepared_session["session_id"],
            "model_name": model["model_name"],
            "predicted_overall_score": round(raw_score, 2),
            "predicted_stars": stars
        }