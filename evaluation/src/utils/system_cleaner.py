import os
import shutil
from pathlib import Path


class SystemCleaner:
    """
    Cleans system artifacts for fresh run
    """

    def __init__(self, config):
        self.config = config

        self.project_root = Path(__file__).resolve().parents[2]

        self.output_dir = Path(config["paths"]["output_dir"])
        self.db_path = Path(config["paths"]["database"])
        self.log_path = self.project_root / "logs" / "evaluationLog.json"

    # =========================================================
    # ================= CLEAN ALL =============================
    # =========================================================

    def clean_all(self):

        print("\nCleaning system for fresh start...\n")

        self._clean_output()
        self._clean_logs()
        self._clean_database()

        print("System cleaned successfully\n")

    # =========================================================
    # ================= OUTPUT ================================
    # =========================================================

    def _clean_output(self):

        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
            print(f"Output directory cleared: {self.output_dir}")

        self.output_dir.mkdir(parents=True, exist_ok=True)

    # =========================================================
    # ================= LOGS ==================================
    # =========================================================

    def _clean_logs(self):

        if self.log_path.exists():
            self.log_path.unlink()
            print(f"Log file removed: {self.log_path}")

    # =========================================================
    # ================= DATABASE ==============================
    # =========================================================

    def _clean_database(self):

        if self.db_path.exists():
            self.db_path.unlink()
            print(f"Database removed: {self.db_path}")