"""Configuration loader for the evaluation system."""

import json
from pathlib import Path


class Config:
    """
    Singleton config loader
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            instance = super().__new__(cls)

            # ================= LOAD CONFIG =================

            # Go from:
            # src/config/config_loader.py
            # -> up to parent of 7-evaluation
            parent_dir = Path(__file__).resolve().parents[3]

            # Build config path
            config_path = parent_dir / "config" / "evaluationConfig.json"

            # Validate file exists
            if not config_path.exists():
                raise FileNotFoundError(f"Config file not found: {config_path}")

            # Load JSON
            with config_path.open("r", encoding="utf-8") as f:
                instance._config = json.load(f)

            cls._instance = instance

        return cls._instance

    # ================= DICT ACCESS =================

    def __getitem__(self, key):
        return self._config[key]

    # ================= OPTIONAL HELPERS =================

    def get(self, key, default=None):
        """Configuration loader for the evaluation system."""
        return self._config.get(key, default)

    def all(self):
        """Return all configuration values."""
        return self._config


