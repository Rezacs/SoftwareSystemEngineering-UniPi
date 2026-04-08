import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from datetime import datetime
import os


class VisualReport:
    """
    Generates dashboard-style evaluation report (PNG)
    """

    def generate(self, batch, config):

        # ================= CONFIG =================
        eval_cfg = config["evaluation"]
        output_dir = config["paths"]["output_dir"]

        os.makedirs(output_dir, exist_ok=True)

        tolerance = eval_cfg["error_threshold"]
        max_errors = eval_cfg["max_errors"]
        max_consec = eval_cfg["max_consecutive_errors"]

        # ================= DATA =================
        table_data = []

        errors = 0
        consecutive = 0
        max_consecutive = 0

        for item in batch:
            pid = item["player_id"]
            expert = item["expert"]
            classifier = item["classifier"]

            diff = abs(expert - classifier)

            th0_status = "OK" if diff <= tolerance else f"ERROR ({diff}>{tolerance})"

            if diff <= tolerance:
                result = "OK"
                consecutive = 0
            else:
                result = "ERROR"
                errors += 1
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)

            table_data.append([
                pid,
                expert,
                classifier,
                diff,
                th0_status,
                result
            ])

        # ================= THRESHOLDS =================
        th1_ok = errors <= max_errors
        th2_ok = max_consecutive <= max_consec

        # ================= FIGURE =================
        fig = plt.figure(figsize=(14, 8))

        fig.text(0.02, 0.94, "Evaluation System Dashboard",
                 fontsize=16, fontweight="bold")

        now = datetime.now()

        fig.text(0.02, 0.90, f"DATE: {now.strftime('%d %b %Y')}")
        fig.text(0.20, 0.90, f"TIME: {now.strftime('%H:%M:%S')}")
        fig.text(0.40, 0.90, f"BATCH SIZE: {len(batch)}")

        # ================= TABLE =================
        ax_table = fig.add_axes([0.02, 0.15, 0.65, 0.7])
        ax_table.axis("off")

        col_labels = [
            "ID", "Expert", "Classifier",
            "Diff", "TH_0", "Result"
        ]

        table = ax_table.table(
            cellText=table_data,
            colLabels=col_labels,
            loc="center",
            cellLoc="center"
        )

        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.5)

        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_facecolor("#4A90E2")
                cell.set_text_props(color="white", weight="bold")
            else:
                result = table_data[row - 1][5]
                cell.set_facecolor("#f8d7da" if result == "ERROR" else "#e8f5e9")

        # ================= RIGHT PANEL =================
        ax_right = fig.add_axes([0.70, 0.15, 0.28, 0.7])
        ax_right.axis("off")

        ax_right.text(0.0, 0.95, "THRESHOLDS",
                      fontsize=12, fontweight="bold")

        ax_right.text(0.0, 0.80,
                      f"TH_0 (error threshold): {tolerance}",
                      bbox=dict(facecolor="#fff3cd", boxstyle="round,pad=0.5"))

        ax_right.text(0.0, 0.65,
                      f"TH_1 (max errors): {max_errors}",
                      bbox=dict(facecolor="#fff3cd", boxstyle="round,pad=0.5"))

        ax_right.text(0.0, 0.50,
                      f"TH_2 (max consecutive): {max_consec}",
                      bbox=dict(facecolor="#fff3cd", boxstyle="round,pad=0.5"))

        # TH_1 result
        ax_right.text(
            0.0, 0.30,
            f"TH_1 {'OK' if th1_ok else 'FAIL'}: {errors}/{max_errors}",
            fontsize=10,
            bbox=dict(
                facecolor="#28a745" if th1_ok else "#dc3545",
                boxstyle="round,pad=0.6"
            ),
            color="white"
        )

        # TH_2 result
        ax_right.text(
            0.0, 0.15,
            f"TH_2 {'OK' if th2_ok else 'FAIL'}: {max_consecutive}/{max_consec}",
            fontsize=10,
            bbox=dict(
                facecolor="#28a745" if th2_ok else "#dc3545",
                boxstyle="round,pad=0.6"
            ),
            color="white"
        )

        # ================= SAVE =================
        filename = os.path.join(
            output_dir,
            f"dashboard_{now.strftime('%Y%m%d_%H%M%S')}.png"
        )

        plt.savefig(filename, bbox_inches="tight")
        plt.close()

        return {
            "file": filename,
            "errors": errors,
            "max_consecutive": max_consecutive
        }