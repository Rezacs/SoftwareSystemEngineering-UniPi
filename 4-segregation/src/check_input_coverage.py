"""Computes input-coverage statistics and report data for the features of the active batch."""

class CheckInputCoverage:
    def analyze_feature(self, values: list[float]) -> dict:
        if not values:
            return {
                "covered": False,
                "min": None,
                "max": None,
                "unique_values": 0
            }

        unique_values = len(set(values))
        min_value = min(values)
        max_value = max(values)

        covered = unique_values > 1 and min_value != max_value

        return {
            "covered": covered,
            "min": min_value,
            "max": max_value,
            "unique_values": unique_values
        }

    def retrieveStatistics(self, feature_map: dict) -> dict:
        return {
            feature_name: self.analyze_feature(values)
            for feature_name, values in feature_map.items()
        }

    def generatePlotData(self, statistics: dict, threshold: float = 0.8) -> dict:
        feature_reports = statistics
        covered_features = sum(
            1 for report in feature_reports.values() if report["covered"]
        )
        coverage_ratio = (
            covered_features / len(feature_reports) if feature_reports else 0
        )
        all_covered = coverage_ratio >= threshold
        uncovered_features = []

        for feature_name, report in feature_reports.items():
            if report["covered"]:
                continue

            if report["unique_values"] == 0:
                comment = "No samples available for this feature"
            else:
                comment = "Feature has insufficient variability across samples"

            uncovered_features.append(
                {
                    "featureName": feature_name,
                    "comment": comment,
                }
            )

        return {
            "approved": all_covered,
            "all_features_covered": all_covered,
            "coverage_ratio": coverage_ratio,
            "coverage_threshold": threshold,
            "uncoveredFeatures": uncovered_features,
            "features": feature_reports
        }

    def build_coverage_report(self, prepared_sessions: list) -> dict:
        statistics = self.retrieveStatistics(prepared_sessions)
        return self.generatePlotData(statistics)
