"""Generates the PNG visualization of the balancing report and supports marking the report as unapproved."""

import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .utils.json_io import JsonIO


class ViewBalancing:
    def _build_distribution(self, balancing_report: dict) -> dict[int, int]:
        raw_distribution = balancing_report.get("distribution", {})
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        for label, value in raw_distribution.items():
            try:
                parsed_label = int(label)
            except (TypeError, ValueError):
                continue
            if parsed_label in distribution:
                distribution[parsed_label] = int(value)

        return distribution

    def showPlot(self, balancing_report: dict, plot_path: str):
        distribution = self._build_distribution(balancing_report)
        labels = [1, 2, 3, 4, 5]
        values = [distribution.get(label, 0) for label in labels]
        total_samples = int(balancing_report.get("totalSamples", sum(values)))
        average = float(balancing_report.get("averageSamplesPerClass", total_samples / len(labels) if labels else 0.0))
        tolerance = float(balancing_report.get("toleranceUsed", balancing_report.get("tolerance", 0.05)))
        tolerance_delta = average * tolerance

        fig = plt.figure(figsize=(9.2, 5.8), facecolor="#ececec")
        ax_chart = fig.add_subplot(111)
        ax_chart.set_facecolor("#f7f7f7")
        max_value = max(values + [average + tolerance_delta, 1.0])
        y_step = max(25, int(math.ceil(max_value / 5 / 25) * 25))
        y_max = int(math.ceil((max_value * 1.15) / y_step) * y_step)

        bar_colors = ["#e3c28f", "#9ecbd2", "#b6ccb5", "#cfc3d9", "#dfb8b8"]
        ax_chart.bar(labels, values, color=bar_colors, edgecolor="#7d7d7d", linewidth=1.1, width=0.65)

        ax_chart.set_xlim(0.4, 5.9)
        ax_chart.set_ylim(0, y_max)
        ax_chart.set_xticks(labels)
        ax_chart.set_xlabel("Classes (player overall)", fontsize=12)
        ax_chart.set_ylabel("Samples number", fontsize=12)
        ax_chart.grid(axis="y", linestyle=(0, (2, 2)), color="#6f6f6f", alpha=0.55)

        ax_chart.axhline(average, color="#3f67e8", linewidth=1.7)
        ax_chart.axhline(average + tolerance_delta, color="#8cc8ff", linewidth=1.4, linestyle=(0, (3, 2)))
        ax_chart.axhline(max(0.0, average - tolerance_delta), color="#8cc8ff", linewidth=1.4, linestyle=(0, (3, 2)))

        ax_chart.text(5.92, average, "Average line", color="#3f67e8", fontsize=12, va="center", ha="left")
        ax_chart.text(5.92, average + tolerance_delta, "Tolerance lines", color="#8cc8ff", fontsize=12, va="center", ha="left")

        ax_chart.spines["top"].set_visible(False)
        ax_chart.spines["right"].set_visible(False)
        ax_chart.spines["left"].set_color("#444444")
        ax_chart.spines["bottom"].set_color("#444444")

        fig.savefig(plot_path, dpi=140, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)

    def setUnbalanced(self, report_path: str):
        balancing_report = JsonIO.load(report_path)
        balancing_report["approved"] = False
        JsonIO.save(report_path, balancing_report)
        return balancing_report
