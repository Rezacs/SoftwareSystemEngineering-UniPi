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

    def build_coverage_report(self, prepared_sessions: list) -> dict:
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

        feature_reports = {
            feature_name: self.analyze_feature(values)
            for feature_name, values in feature_map.items()
        }

        all_covered = all(report["covered"] for report in feature_reports.values())

        return {
            "all_features_covered": all_covered,
            "features": feature_reports
        }