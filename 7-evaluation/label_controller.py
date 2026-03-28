from .utils.json_io import JsonIO


class LabelController:
    def load_prediction_result(self, path: str) -> dict:
        return JsonIO.load(path)

    def build_label_pair(self, prediction_result: dict) -> dict:
        predicted_stars = prediction_result["predicted_stars"]

        expert_stars = predicted_stars

        return {
            "player_id": prediction_result["player_id"],
            "session_id": prediction_result["session_id"],
            "expert_label": expert_stars,
            "classifier_label": predicted_stars
        }
