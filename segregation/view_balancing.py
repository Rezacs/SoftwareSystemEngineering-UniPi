"""Generates the PNG visualization of the balancing report and supports marking the report as unapproved."""

from .utils.json_io import JsonIO
from .utils.png_canvas import PngCanvas


class ViewBalancing:
    def showPlot(self, balancing_report: dict, plot_path: str):
        distribution = balancing_report.get("distribution", {})
        labels = ["1_star", "2_star", "3_star", "4_star", "5_star"]
        values = [distribution.get(label, 0) for label in labels]
        max_value = max(values) if values else 0

        canvas = PngCanvas(640, 360, background=(248, 249, 251))
        canvas.fill_rect(0, 0, 640, 40, (29, 78, 216))
        canvas.draw_horizontal_line(60, 300, 520, (30, 41, 59))
        canvas.draw_vertical_line(60, 60, 240, (30, 41, 59))

        bar_width = 70
        gap = 28
        start_x = 90
        bar_color = (34, 197, 94) if balancing_report.get("approved", False) else (239, 68, 68)

        for index, value in enumerate(values):
            height = 0
            if max_value > 0:
                height = int((value / max_value) * 200)
            x = start_x + index * (bar_width + gap)
            y = 300 - height
            canvas.fill_rect(x, y, bar_width, height, bar_color)
            canvas.fill_rect(x, 305, bar_width, 12, (148, 163, 184))

        canvas.save(plot_path)

    def setUnbalanced(self, report_path: str):
        balancing_report = JsonIO.load(report_path)
        balancing_report["approved"] = False
        JsonIO.save(report_path, balancing_report)
        return balancing_report
