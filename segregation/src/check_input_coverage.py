"""Computes input-coverage statistics and report data for the features of the active batch."""

import math

class CheckInputCoverage:
    def analyze_feature(self, values: list[float]) -> dict:
        if not values:
            return {
                "covered": False,
                "min": None,
                "max": None,
                "unique_values": 0,
                "normalized_values": []
            }

        numeric_values = []
        for value in values:
            try:
                parsed_value = float(value)
            except (TypeError, ValueError):
                continue

            if not math.isfinite(parsed_value):
                continue

            numeric_values.append(parsed_value)

        if not numeric_values:
            return {
                "covered": False,
                "min": None,
                "max": None,
                "unique_values": 0,
                "normalized_values": []
            }

        unique_values = len(set(numeric_values))
        min_value = min(numeric_values)
        max_value = max(numeric_values)

        covered = unique_values > 1 and min_value != max_value

        if max_value == min_value:
            normalized_values = [0.0 for _ in numeric_values]
        else:
            denominator = max_value - min_value
            normalized_values = [
                (value - min_value) / denominator
                for value in numeric_values
            ]

        return {
            "covered": covered,
            "min": min_value,
            "max": max_value,
            "unique_values": unique_values,
            "normalized_values": normalized_values,
        }

    def retrieveStatistics(self, feature_map: dict) -> dict:
        return {
            feature_name: self.analyze_feature(values)
            for feature_name, values in feature_map.items()
        }

    def generatePlotData(self, statistics: dict) -> dict:
        return {
            "features": statistics,
        }

    def build_coverage_report(self, prepared_sessions: list) -> dict:
        statistics = self.retrieveStatistics(prepared_sessions)
        return self.generatePlotData(statistics)
