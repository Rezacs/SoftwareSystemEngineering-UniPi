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

    def retrieveStatistics(self, prepared_sessions: list) -> dict:
        feature_map = {
            "skill_overall": [],
            "social_influence_score": [],
            "injuries_impact_score": []
        }

        for session in prepared_sessions:
            features = session.get("features", {})
            for key in feature_map:
                value = features.get(key)
                if value is not None:
                    feature_map[key].append(value)

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

        return {
            "all_features_covered": all_covered,
            "coverage_ratio": coverage_ratio,
            "coverage_threshold": threshold,
            "features": feature_reports
        }

    def build_coverage_report(self, prepared_sessions: list) -> dict:
        statistics = self.retrieveStatistics(prepared_sessions)
        return self.generatePlotData(statistics)
