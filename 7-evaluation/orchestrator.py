from evaluation.label_controller import LabelController
from evaluation.buffer_controller import BufferController
from evaluation.evaluation_controller import EvaluationController
from evaluation.report_controller import ReportController



class EvaluationSystemOrchestrator:
    def __init__(self):
        self.label_controller = LabelController()
        self.buffer_controller = BufferController()
        self.evaluation_controller = EvaluationController()
        self.report_controller = ReportController()

    def run(
        self,
        prediction_result_path="data/outputs/prediction_result.json",
        buffer_path="data/outputs/evaluation_buffer.json",
        report_path="data/outputs/evaluation_report.json"
    ):
        prediction_result = self.label_controller.load_prediction_result(prediction_result_path)
        label_pair = self.label_controller.build_label_pair(prediction_result)

        buffer_data = self.buffer_controller.add_label_pair(label_pair, buffer_path)

        evaluation_result = self.evaluation_controller.evaluate(buffer_data)
        report = self.report_controller.build_report(evaluation_result)
        self.report_controller.save_report(report, report_path)

        return report