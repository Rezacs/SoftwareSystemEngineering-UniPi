from .utils.json_io import JsonIO


class PredictionResultSender:
    def send_result(self, prediction_result: dict, output_path: str) -> None:
        JsonIO.save(output_path, prediction_result)
