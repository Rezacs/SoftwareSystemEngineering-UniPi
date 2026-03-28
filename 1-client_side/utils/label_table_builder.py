from .feature_extractor import compute_feature_scores


class LabelTableBuilder:
    def compute_label(self, record: dict) -> str:
        skill_overall, social_influence_score, injuries_impact_score = (
            compute_feature_scores(record)
        )

        raw_score = (
            (0.6 * skill_overall)
            + (0.3 * social_influence_score / 1000)
            - (0.1 * injuries_impact_score / 100)
        )
        raw_score = max(0, min(raw_score, 100))

        if raw_score < 20:
            return "1_star"
        if raw_score < 40:
            return "2_star"
        if raw_score < 60:
            return "3_star"
        if raw_score < 80:
            return "4_star"
        return "5_star"

    def build_map(self, label_rows: list[dict]) -> dict:
        return {
            row["player_id"]: row["label"]
            for row in label_rows
            if "player_id" in row and "label" in row
        }

