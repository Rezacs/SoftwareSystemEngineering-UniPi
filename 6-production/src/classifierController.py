import json
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd

from src.config import CLASSIFIERS_DIR, FEATURE_COLUMNS, LATEST_CLASSIFIER_PATH


class ClassifierController:
    def __init__(self):
        self.active_classifier_path = None
        self.active_classifier_id = None
        self.model = None
        self._load_latest_classifier()

    def _load_latest_classifier(self):
        if not LATEST_CLASSIFIER_PATH.exists():
            print("[ClassifierController] No latest classifier metadata found.")
            return

        try:
            with open(LATEST_CLASSIFIER_PATH, "r", encoding="utf-8") as file:
                metadata = json.load(file)
        except Exception as e:
            print(f"[ClassifierController] Failed to read latest classifier metadata: {e}")
            return

        classifier_path_value = metadata.get("classifier_path")
        if not classifier_path_value:
            print("[ClassifierController] No classifier_path in latest classifier metadata.")
            return

        classifier_path = Path(classifier_path_value)

        if not classifier_path.exists():
            print(f"[ClassifierController] Saved classifier file not found: {classifier_path}")
            return

        try:
            self.model = joblib.load(classifier_path)
            self.active_classifier_path = classifier_path
            self.active_classifier_id = metadata.get("classifier_id")
            print(f"[ClassifierController] Active classifier loaded at startup: {self.active_classifier_id}")
        except Exception as e:
            print(f"[ClassifierController] Failed to load classifier model: {e}")

    def save_uploaded_classifier(self, uploaded_file):
        model_filename = uploaded_file.filename
        classifier_id = Path(model_filename).stem
        destination_path = CLASSIFIERS_DIR / model_filename

        uploaded_file.save(destination_path)
        print(f"[ClassifierController] Uploaded classifier saved to: {destination_path}")

        metadata = {
            "classifier_id": classifier_id,
            "model_filename": model_filename,
            "classifier_path": str(destination_path.resolve()),
            "deployment_timestamp": datetime.now().isoformat(),
            "active": True
        }

        with open(LATEST_CLASSIFIER_PATH, "w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=4)

        print(f"[ClassifierController] Classifier metadata written to: {LATEST_CLASSIFIER_PATH}")
        return metadata

    def deploy_classifier(self, classifier_id: str, model_filename: str):
        classifier_path = CLASSIFIERS_DIR / model_filename

        if not classifier_path.exists():
            raise FileNotFoundError(f"Classifier file not found: {classifier_path}")

        self.model = joblib.load(classifier_path)
        self.active_classifier_path = classifier_path
        self.active_classifier_id = classifier_id

        deployment_info = {
            "classifier_id": classifier_id,
            "model_filename": model_filename,
            "classifier_path": str(classifier_path.resolve()),
            "deployment_timestamp": datetime.now().isoformat(),
            "status": "deployed"
        }

        print(f"[ClassifierController] Classifier deployed: {classifier_id}")
        return deployment_info

    def classify(self, prepared_session: dict):
        if self.model is None:
            raise RuntimeError("No deployed classifier available.")

        input_row = {feature: prepared_session[feature] for feature in FEATURE_COLUMNS}
        input_frame = pd.DataFrame([input_row])

        predicted_rating = float(self.model.predict(input_frame)[0])

        result = {
            "player_id": prepared_session["playerID"],
            "source": "classifier",
            "rating": predicted_rating,
            "classifier_id": self.active_classifier_id,
            "classification_timestamp": datetime.now().isoformat()
        }

        print(f"[ClassifierController] Classification result: {result}")
        return result