import time
import json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple
from backend.app.core.config import MODELS_DIR, CLINICAL_SAFETY_DISCLAIMER

class ParkinsonVoiceClassifier:
    _instance = None

    def __init__(self):
        self.model_path = MODELS_DIR / "model.joblib"
        self.scaler_path = MODELS_DIR / "scaler.joblib"
        self.features_path = MODELS_DIR / "features.json"
        self.metrics_path = MODELS_DIR / "metrics.json"

        self.model = None
        self.scaler = None
        self.feature_names = []
        self.model_version = "rf-gb-svm-v2.0.0-multidataset"

        self._ensure_loaded()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ParkinsonVoiceClassifier()
        return cls._instance

    def _ensure_loaded(self):
        if not self.model_path.exists() or not self.scaler_path.exists():
            print("[ML] Trained model artifacts not found. Initiating training...")
            from backend.app.ml.train_classifier import train_and_evaluate_model
            train_and_evaluate_model()

        self.model = joblib.load(self.model_path)
        self.scaler = joblib.load(self.scaler_path)

        if self.features_path.exists():
            with open(self.features_path, "r") as f:
                self.feature_names = json.load(f)
        else:
            from backend.app.ml.train_classifier import FEATURE_COLS
            self.feature_names = FEATURE_COLS

    def predict_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs inference on an extracted feature dictionary.
        Returns risk score, confidence, severity level, inference time in ms, and clinical disclaimer.
        """
        start_time = time.perf_counter()

        # Build feature dataframe matching training order and column names
        row_dict = {}
        for feat in self.feature_names:
            val = features.get(feat)
            if val is None:
                val = 0.0
            row_dict[feat] = [float(val)]

        df_input = pd.DataFrame(row_dict)
        X_scaled_arr = self.scaler.transform(df_input)
        X_scaled = pd.DataFrame(X_scaled_arr, columns=df_input.columns)

        # Soft probability prediction: [P(healthy), P(PD_risk)]
        probabilities = self.model.predict_proba(X_scaled)[0]
        risk_score = float(probabilities[1])

        # Confidence metric based on margin from decision boundary (0.5)
        raw_margin = abs(risk_score - 0.5) * 2.0  # 0 to 1
        confidence = float(min(1.0, 0.70 + raw_margin * 0.30))  # baseline confidence 70-100%

        # Map to human-readable severity level
        if risk_score < 0.35:
            severity_level = "LOW_RISK"
        elif risk_score < 0.60:
            severity_level = "MILD"
        elif risk_score < 0.80:
            severity_level = "MODERATE"
        else:
            severity_level = "SEVERE"

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        return {
            "risk_score": round(risk_score, 4),
            "confidence": round(confidence, 4),
            "severity_level": severity_level,
            "model_version": self.model_version,
            "inference_time_ms": elapsed_ms,
            "disclaimer": CLINICAL_SAFETY_DISCLAIMER
        }

classifier = ParkinsonVoiceClassifier.get_instance()
