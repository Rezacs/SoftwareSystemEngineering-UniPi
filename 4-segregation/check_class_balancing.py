class CheckClassBalancing:
    def assign_label(self, prepared_session: dict) -> str:
        score = prepared_session["features"]["skill_overall"]

        if score < 20:
            return "1_star"
        elif score < 40:
            return "2_star"
        elif score < 60:
            return "3_star"
        elif score < 80:
            return "4_star"
        else:
            return "5_star"

    def build_distribution(self, prepared_sessions: list) -> dict:
        distribution = {
            "1_star": 0,
            "2_star": 0,
            "3_star": 0,
            "4_star": 0,
            "5_star": 0
        }

        for session in prepared_sessions:
            label = self.assign_label(session)
            distribution[label] += 1

        return distribution

    def check_balance(self, distribution: dict, tolerance: float = 0.05) -> dict:
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