"""
config.py
=========
Single source of truth for all configuration.
Loads Data/configs/config.json once at import time and exposes
typed constants that every other module imports directly.

Usage:
    from src.config import PATHS, NETWORK, PIPELINE, MODEL
"""

import json
import os

# ── Location of the config file ────────────────────────────────────────────
_CONFIG_PATH = os.path.join("Data", "configs", "config.json")


def _load() -> dict:
    if not os.path.isfile(_CONFIG_PATH):
        raise FileNotFoundError(
            f"Configuration file not found: {_CONFIG_PATH}\n"
            f"Make sure config.json exists before running the application."
        )
    with open(_CONFIG_PATH, "r", encoding="UTF-8") as f:
        return json.load(f)


_cfg = _load()

# ── Typed accessors ────────────────────────────────────────────────────────

# Network
NETWORK = _cfg["network"]

LISTEN_HOST = NETWORK["listen_host"]
LISTEN_PORT = int(NETWORK["listen_port"])

SEGREGATION_SYSTEM_IP   = NETWORK["segregation_system"]["ip"]
SEGREGATION_SYSTEM_PORT = int(NETWORK["segregation_system"]["port"])

PRODUCTION_SYSTEM_IP   = NETWORK["production_system"]["ip"]
PRODUCTION_SYSTEM_PORT = int(NETWORK["production_system"]["port"])
PRODUCTION_ENDPOINT    = NETWORK["production_system"]["endpoint"]

MESSAGING_SYSTEM_IP   = NETWORK["messaging_system"]["ip"]
MESSAGING_SYSTEM_PORT = int(NETWORK["messaging_system"]["port"])
MESSAGING_ENDPOINT    = NETWORK["messaging_system"]["endpoint"]

# Paths
PATHS = _cfg["paths"]

DATA_FOLDER            = PATHS["data_folder"]
STATUS_FILE_PATH       = PATHS["status_file"]
CLASSIFIER_FOLDER      = PATHS["classifier_folder"]
LEARNING_CURVE_PATH    = PATHS["learning_curve"]
VALIDATION_REPORT_PATH = PATHS["validation_report"]
TESTING_REPORT_PATH    = PATHS["testing_report"]
USER_INPUT_PATH        = PATHS["user_input"]
RECEIVED_DATA_PATH     = PATHS["received_data"]
LEARNING_SETS_PATH     = PATHS["learning_sets"]

# Model
MODEL = _cfg["model"]

FEATURE_COLS = MODEL["feature_cols"]
SCORE_MIN    = int(MODEL["score_min"])
SCORE_MAX    = int(MODEL["score_max"])

# Pipeline
PIPELINE = _cfg["pipeline"]

OVERFITTING_THRESHOLD    = float(PIPELINE["overfitting_threshold"])
GENERALIZATION_THRESHOLD = float(PIPELINE["generalization_threshold"])
MAX_OUTER_ITERATIONS     = int(PIPELINE["max_outer_iterations"])
DEFAULT_MAX_ITER         = int(PIPELINE["default_max_iter"])