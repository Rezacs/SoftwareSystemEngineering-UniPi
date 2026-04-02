import json
import shutil
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd

from src.config import (
    CLASSIFIERS_DIR,
    FEATURE_COLUMNS,
    LATEST_CLASSIFIER_PATH,
)


class ClassifierController:
    def __init__(self):
        self.active_classifier_path = None
        self.active_classifier_id = None
        self.model = None
        self._load_latest_classifier()

    def _load_latest_classifier(self):
        if not LATEST_CLASSIFIER_PATH.exists():
            return

        with open(LATEST_CLASSIFIER_PATH, "r", encoding="utf-8") as file:
            metadata = json.load(file)

        # ✅ SAFE CHECK
        if "classifier_path" not in metadata:
            return

        classifier_path = Path(metadata["classifier_path"])

        if classifier_path.exists():
            self.active_classifier_path = classifier_path
            self.active_classifier_id = metadata.get("classifier_id")
            self.model = joblib.load(classifier_path)

    def save_classifier(self, source_model_path: str, classifier_id: str, model_filename: str):
        source_path = Path(source_model_path)
        destination_path = CLASSIFIERS_DIR / model_filename

        shutil.copy(source_path, destination_path)

        metadata = {
            "classifier_id": classifier_id,
            "model_filename": model_filename,
            "classifier_path": str(destination_path),
            "deployment_timestamp": datetime.now().isoformat(),
            "active": True
        }

        with open(LATEST_CLASSIFIER_PATH, "w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=4)

        return destination_path, metadata

    def deploy_classifier(self, classifier_id: str, model_filename: str):
        classifier_path = CLASSIFIERS_DIR / model_filename

        if not classifier_path.exists():
            raise FileNotFoundError(f"Classifier file not found: {classifier_path}")

        self.model = joblib.load(classifier_path)
        self.active_classifier_path = classifier_path
        self.active_classifier_id = classifier_id

        return {
            "classifier_id": classifier_id,
            "model_filename": model_filename,
            "classifier_path": str(classifier_path),
            "deployment_timestamp": datetime.now().isoformat(),
            "status": "deployed"
        }

    def classify(self, prepared_session: dict):
        if self.model is None:
            raise RuntimeError("No deployed classifier available.")

        input_row = {feature: prepared_session[feature] for feature in FEATURE_COLUMNS}
        input_frame = pd.DataFrame([input_row])

        predicted_label = self.model.predict(input_frame)[0]

        return {
            "session_uuid": prepared_session["session_uuid"],
            "classifier_id": self.active_classifier_id,
            "predicted_label": int(predicted_label),
            "classification_timestamp": datetime.now().isoformat()
        }