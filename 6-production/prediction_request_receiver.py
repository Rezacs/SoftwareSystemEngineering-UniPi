from .utils.json_io import JsonIO


class PredictionRequestReceiver:
    def receive_prepared_session(self, path: str) -> dict:
        return JsonIO.load(path)

    def receive_selected_model(self, path: str) -> dict:
        report = JsonIO.load(path)
        return report["best_model"]
