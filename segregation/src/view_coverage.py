"""Generates the PNG visualization of the coverage report and supports marking the report as unapproved."""

import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .utils.json_io import JsonIO


class ViewCoverage:
    def showPlot(self, coverage_report: dict, plot_path: str):
        features = coverage_report.get("features", {})
        feature_stats = list(features.items())
        feature_names = [name for name, _ in feature_stats]
        total_features = len(feature_stats)
        if total_features == 0:
            fig = plt.figure(figsize=(7.5, 6.2), facecolor="#ececec")
            ax = fig.add_subplot(111)
            ax.set_facecolor("#f7f7f7")
            ax.axis("off")
            ax.text(0.5, 0.5, "No features available", ha="center", va="center", fontsize=15, color="#555555")
            fig.savefig(plot_path, dpi=140, bbox_inches="tight", facecolor=fig.get_facecolor())
            plt.close(fig)
            return

        angles = [2 * math.pi * i / total_features for i in range(total_features)]

        fig = plt.figure(figsize=(8.4, 7.0), facecolor="#ececec")
        ax = fig.add_subplot(111, polar=True)
        ax.set_facecolor("#f7f7f7")
        ax.set_ylim(0.0, 1.0)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], color="#666666", fontsize=9)
        ax.set_xticks(angles)
        tick_labels = ax.set_xticklabels(feature_names, fontsize=11, color="#404040")
        ax.tick_params(axis="x", pad=16)

        # Move only the top label slightly downward to avoid overlap with plotted points.
        for index, feature_name in enumerate(feature_names):
            if feature_name == "skill_overall":
                current_x, current_y = tick_labels[index].get_position()
                tick_labels[index].set_position((current_x, current_y - 0.08))
                tick_labels[index].set_va("top")
                break

        ax.grid(color="#b6b6b6", linestyle="-", linewidth=1.0, alpha=0.7)

        # Plot only sample points on each feature axis (no polygon connection between maxima).
        for idx, (_, data) in enumerate(feature_stats):
            normalized_values = data.get("normalized_values") or []
            if not normalized_values:
                ax.scatter([angles[idx]], [0.0], color="#2447e3", s=18, alpha=0.75, zorder=2)
                continue

            radii = [max(0.0, min(1.0, float(value))) for value in normalized_values]
            angle_list = [angles[idx] for _ in radii]
            ax.scatter(angle_list, radii, color="#2447e3", s=18, alpha=0.75, zorder=2)

        fig.savefig(plot_path, dpi=140, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)

    def setUncovered(self, report_path: str):
        coverage_report = JsonIO.load(report_path)
        coverage_report["approved"] = False
        JsonIO.save(report_path, coverage_report)
        return coverage_report
