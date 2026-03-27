class CheckClassBalancing:
    def retrieveLabels(self, prepared_sessions: list) -> list[str]:
        labels = []
        for session in prepared_sessions:
            label = session.get("label")
            if label is not None:
                labels.append(label)
        return labels

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
                "balanced": False,
                "tolerance": tolerance,
                "distribution": distribution,
                "average": 0,
                "details": "No data available"
            }

        average = total / len(counts)

        balanced = all(
            abs(count - average) <= (average * tolerance)
            for count in counts
        )

        return {
            "balanced": balanced,
            "tolerance": tolerance,
            "distribution": distribution,
            "average": average
        }

    def build_distribution(self, prepared_sessions: list) -> dict:
        labels = self.retrieveLabels(prepared_sessions)
        return self.generatePlotData(labels)["distribution"]

    def check_balance(self, distribution: dict, tolerance: float = 0.05) -> dict:
        labels = []
        for label, count in distribution.items():
            labels.extend([label] * count)
        return self.generatePlotData(labels, tolerance)
