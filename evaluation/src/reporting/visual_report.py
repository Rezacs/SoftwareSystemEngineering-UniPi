import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path


class VisualReport:
   
    def generate(self, batch, config):

        # ================= CONFIG =================
        eval_cfg = config["evaluation"]
        output_dir = Path(config["paths"]["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

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

            th0_status = "OK" if diff <= tolerance else f"ERR"

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

        # ================= FIGURE (A4 STYLE) =================
        fig = plt.figure(figsize=(11.7, 8.3))  # A4 landscape

        now = datetime.now()

        # ================= HEADER =================
        fig.text(0.02, 0.96, "Evaluation System Dashboard",
                 fontsize=16, fontweight="bold")

        fig.text(0.02, 0.92, f"DATE: {now.strftime('%d %b %Y')}")
        fig.text(0.25, 0.92, f"TIME: {now.strftime('%H:%M:%S')}")
        fig.text(0.45, 0.92, f"BATCH SIZE: {len(batch)}")

        # ================= TABLE AREA =================
        ax_table = fig.add_axes([0.02, 0.08, 0.72, 0.80])
        ax_table.axis("off")

        col_labels = ["ID", "Expert", "Classifier", "Diff", "TH_0", "Result"]

        # Adaptive scaling based on size
        if len(table_data) <= 10:
            font_size = 10
            scale_y = 1.5
        elif len(table_data) <= 25:
            font_size = 8
            scale_y = 1.2
        else:
            font_size = 6
            scale_y = 1.0

        table = ax_table.table(
            cellText=table_data,
            colLabels=col_labels,
            loc="center",
            cellLoc="center"
        )

        table.auto_set_font_size(False)
        table.set_fontsize(font_size)
        table.scale(1, scale_y)

        # ================= TABLE STYLE =================
        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_facecolor("#2E86C1")
                cell.set_text_props(color="white", weight="bold")
            else:
                result = table_data[row - 1][5]
                cell.set_facecolor("#FADBD8" if result == "ERROR" else "#D5F5E3")

        # ================= RIGHT PANEL =================
        ax_right = fig.add_axes([0.76, 0.08, 0.22, 0.80])
        ax_right.axis("off")

        ax_right.text(0.0, 0.95, "THRESHOLDS",
                      fontsize=12, fontweight="bold")

        def box(y, text):
            ax_right.text(
                0.0, y, text,
                fontsize=9,
                bbox=dict(facecolor="#FCF3CF", boxstyle="round,pad=0.4")
            )

        box(0.80, f"TH_0: {tolerance}")
        box(0.70, f"TH_1: {max_errors}")
        box(0.60, f"TH_2: {max_consec}")

        # ================= RESULT BADGES =================
        def badge(y, text, ok):
            ax_right.text(
                0.0, y, text,
                fontsize=10,
                color="white",
                bbox=dict(
                    facecolor="#28a745" if ok else "#dc3545",
                    boxstyle="round,pad=0.6"
                )
            )

        badge(0.40, f"TH_1 {'OK' if th1_ok else 'FAIL'}: {errors}/{max_errors}", th1_ok)
        badge(0.25, f"TH_2 {'OK' if th2_ok else 'FAIL'}: {max_consecutive}/{max_consec}", th2_ok)

        # ================= SAVE =================
        filename = output_dir / f"dashboard_{now.strftime('%Y%m%d_%H%M%S')}.png"

        plt.savefig(filename, bbox_inches="tight")
        plt.close()

        return {
            "file": str(filename),
            "errors": errors,
            "max_consecutive": max_consecutive
        }