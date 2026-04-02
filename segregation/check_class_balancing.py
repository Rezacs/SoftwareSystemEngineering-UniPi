"""Computes class-balancing statistics and report data starting from the labels of the active batch."""

class CheckClassBalancing:
    def _build_class_statistics(self, distribution: dict, average: float) -> list[dict]:
        class_statistics = []

        for label, num_samples in distribution.items():
            class_label = int(label.split("_")[0])
            missing_samples = max(0, int(round(average - num_samples)))
            excessive_samples = max(0, int(round(num_samples - average)))
            class_statistics.append(
                {
                    "classLabel": class_label,
                    "numSamples": num_samples,
                    "missingSamples": missing_samples,
                    "excessiveSamples": excessive_samples,
                }
            )

        return class_statistics

    def retrieveLabels(self, labels: list[str]) -> list[str]:
        return [label for label in labels if label is not None]

    def generatePlotData(self, labels: list[str], tolerance: float = 0.05) -> dict:
        distribution = {
            "1_star": 0,
            "2_star": 0,
            "3_star": 0,
            "4_star": 0,
            "5_star": 0
        }

        for label in labels:
            if label in distribution:
                distribution[label] += 1
        counts = list(distribution.values())
        total = sum(counts)

        if total == 0:
            return {
                "approved": False,
                "balanced": False,
                "totalSamples": 0,
                "tolerance": tolerance,
                "toleranceUsed": tolerance,
                "distribution": distribution,
                "average": 0,
                "averageSamplesPerClass": 0,
                "classStatistics": self._build_class_statistics(distribution, 0),
                "details": "No data available"
            }

        average = total / len(counts)

        balanced = all(
            abs(count - average) <= (average * tolerance)
            for count in counts
        )

        return {
            "approved": balanced,
            "balanced": balanced,
            "totalSamples": total,
            "tolerance": tolerance,
            "toleranceUsed": tolerance,
            "distribution": distribution,
            "average": average,
            "averageSamplesPerClass": average,
            "classStatistics": self._build_class_statistics(distribution, average),
        }

    def build_distribution(self, prepared_sessions: list) -> dict:
        labels = self.retrieveLabels(prepared_sessions)
        return self.generatePlotData(labels)["distribution"]

    def check_balance(self, distribution: dict, tolerance: float = 0.05) -> dict:
        labels = []
        for label, count in distribution.items():
            labels.extend([label] * count)
        return self.generatePlotData(labels, tolerance)
