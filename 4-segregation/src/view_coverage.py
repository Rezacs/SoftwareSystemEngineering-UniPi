"""Generates the PNG visualization of the coverage report and supports marking the report as unapproved."""

from .utils.json_io import JsonIO
from .utils.png_canvas import PngCanvas


class ViewCoverage:
    def showPlot(self, coverage_report: dict, plot_path: str):
        features = coverage_report.get("features", {})
        feature_names = list(features.keys())
        canvas = PngCanvas(640, 360, background=(248, 249, 251))
        canvas.fill_rect(0, 0, 640, 40, (14, 116, 144))
        canvas.draw_horizontal_line(60, 300, 520, (30, 41, 59))

        start_x = 90
        box_width = 120
        gap = 35

        for index, feature_name in enumerate(feature_names):
            feature_data = features[feature_name]
            color = (34, 197, 94) if feature_data.get("covered", False) else (239, 68, 68)
            x = start_x + index * (box_width + gap)
            canvas.fill_rect(x, 120, box_width, 120, color)
            canvas.fill_rect(x, 255, box_width, 12, (148, 163, 184))

        canvas.save(plot_path)

    def setUncovered(self, report_path: str):
        coverage_report = JsonIO.load(report_path)
        coverage_report["approved"] = False
        JsonIO.save(report_path, coverage_report)
        return coverage_report
