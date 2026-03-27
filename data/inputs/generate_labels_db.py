import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = ROOT / "data" / "inputs"
OUTPUT_PATH = INPUT_DIR / "labels_db.json"


def load_csv_rows(path: Path, player_id_key: str) -> dict[int, dict]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        return {
            int(row[player_id_key]): row
            for row in reader
        }


def compute_label(football: dict, medical: dict, social: dict) -> str:
    shooting = float(football.get("shooting", 0) or 0)
    passing = float(football.get("passing", 0) or 0)
    dribbling = float(football.get("dribbling", 0) or 0)
    defending = float(football.get("defending", 0) or 0)
    physic = float(football.get("physic", 0) or 0)

    number_of_likes = float(social.get("numberOfLikes", 0) or 0)
    number_of_followers = float(social.get("numberOfFollowers", 0) or 0)

    days_missed = float(medical.get("days_missed", 0) or 0)
    games_missed = float(medical.get("games_missed", 0) or 0)

    skill_overall = (shooting + passing + dribbling + defending + physic) / 5
    social_influence_score = (0.7 * number_of_followers) + (0.3 * number_of_likes)
    injuries_impact_score = (0.7 * games_missed) + (0.3 * days_missed)

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


def main():
    football_rows = load_csv_rows(INPUT_DIR / "raws_football_db.csv", "player_id")
    medical_rows = load_csv_rows(INPUT_DIR / "raws_medical_db.csv", "player_id")
    social_rows = load_csv_rows(INPUT_DIR / "raws_social_db.csv", "id_player")

    all_ids = sorted(set(football_rows) | set(medical_rows) | set(social_rows))
    label_rows = []

    for player_id in all_ids:
        label_rows.append(
            {
                "player_id": player_id,
                "label": compute_label(
                    football_rows.get(player_id, {}),
                    medical_rows.get(player_id, {}),
                    social_rows.get(player_id, {}),
                ),
                "label_source": "precomputed_weighted_formula",
            }
        )

    with OUTPUT_PATH.open("w", encoding="utf-8") as output_file:
        json.dump(label_rows, output_file, indent=4)


if __name__ == "__main__":
    main()
