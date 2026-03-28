def compute_feature_scores(record: dict) -> tuple[float, float, float]:
    football = record.get("football") or {}
    medical = record.get("medical") or {}
    social = record.get("social") or {}

    shooting = float(football.get("shooting", 0) or 0)
    passing = float(football.get("passing", 0) or 0)
    dribbling = float(football.get("dribbling", 0) or 0)
    defending = float(football.get("defending", 0) or 0)
    physic = float(football.get("physic", 0) or 0)

    number_of_likes = float(social.get("number_of_likes", 0) or 0)
    number_of_followers = float(social.get("number_of_followers", 0) or 0)

    days_missed = float(medical.get("days_missed", 0) or 0)
    games_missed = float(medical.get("games_missed", 0) or 0)

    skill_overall = (shooting + passing + dribbling + defending + physic) / 5
    social_influence_score = (0.7 * number_of_followers) + (0.3 * number_of_likes)
    injuries_impact_score = (0.7 * games_missed) + (0.3 * days_missed)

    return skill_overall, social_influence_score, injuries_impact_score

