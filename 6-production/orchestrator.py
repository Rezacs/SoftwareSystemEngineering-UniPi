from production.prediction_request_receiver import PredictionRequestReceiver
from production.prediction_executor import PredictionExecutor
from production.prediction_result_sender import PredictionResultSender


class ProductionSystemOrchestrator:
    def __init__(self):
        self.receiver = PredictionRequestReceiver()
        self.executor = PredictionExecutor()
        self.sender = PredictionResultSender()

    def run(
        self,
        prepared_session_path="data/outputs/prepared_session.json",
        validation_report_path="data/outputs/validation_report.json",
        output_path="data/outputs/prediction_result.json"
    ):
        prepared_session = self.receiver.receive_prepared_session(prepared_session_path)
        selected_model = self.receiver.receive_selected_model(validation_report_path)

        prediction_result = self.executor.predict(prepared_session, selected_model)
        self.sender.send_result(prediction_result, output_path)

        return prediction_result