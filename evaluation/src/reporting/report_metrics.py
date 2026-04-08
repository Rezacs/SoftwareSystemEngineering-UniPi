class ReportMetrics:
    """
    Computes evaluation metrics (stateless, config-driven)
    """

    def compute(self, batch, tolerance):

        errors = 0
        consecutive = 0
        max_consecutive = 0

        for item in batch:

            diff = abs(item["expert"] - item["classifier"])

            if diff <= tolerance:
                consecutive = 0
            else:
                errors += 1
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)

        return {
            "total_samples": len(batch),
            "errors": errors,
            "max_consecutive": max_consecutive
        }