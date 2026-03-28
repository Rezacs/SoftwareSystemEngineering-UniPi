from .utils.json_io import JsonIO


class ReportController:
    def build_report(
        self,
        evaluation_result: dict,
        max_total_errors_threshold: int = 5,
        max_consecutive_errors_threshold: int = 3
    ) -> dict:
        total_errors_ok = (
            evaluation_result["total_errors"] <= max_total_errors_threshold
        )
        consecutive_errors_ok = (
            evaluation_result["max_consecutive_errors"] <= max_consecutive_errors_threshold
        )

        accepted = total_errors_ok and consecutive_errors_ok

        return {
            "evaluation_result": evaluation_result,
            "thresholds": {
                "max_total_errors_threshold": max_total_errors_threshold,
                "max_consecutive_errors_threshold": max_consecutive_errors_threshold
            },
            "accepted": accepted
        }

    def save_report(self, report: dict, path: str) -> None:
        JsonIO.save(path, report)
