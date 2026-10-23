import time
from typing import Any, Dict, Optional

import pandas as pd

from ml.data.validator import EXPECTED_FEATURE_COLUMNS, DatasetValidator
from ml.explainability.explainer import ModelExplainer
from ml.registry.metadata import ModelRegistry


class ModelNotAvailableError(Exception):
    """Raised when an inference request is made but no verified model has been trained/loaded."""

    pass


class FraudPredictor:
    """Production-grade inference engine providing score estimation, thresholding, and explanations."""

    @classmethod
    def predict(
        cls,
        features: Dict[str, Any],
        decision_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Assess a single transaction's risk score and feature contributions."""
        # 1. Feature schema and numeric validation
        is_valid, errors, cleaned = DatasetValidator.validate_inference_features(features)
        if not is_valid:
            raise ValueError(f"Feature validation error: {'; '.join(errors)}")

        # 2. Retrieve verified active model artifact
        active = ModelRegistry.load_active_model()
        if not active:
            raise ModelNotAvailableError(
                "No trained model artifact is currently registered. Please train a model via CLI or the Models section."
            )

        pipeline, metadata = active

        # Determine threshold
        if decision_threshold is None:
            threshold = float(metadata.get("decision_threshold", 0.50))
        else:
            threshold = float(decision_threshold)
            threshold = max(0.01, min(0.99, threshold))

        # 3. Format input for scikit-learn pipeline
        df_input = pd.DataFrame([cleaned])[EXPECTED_FEATURE_COLUMNS]

        # 4. Measure execution latency
        start_time = time.perf_counter()
        probabilities = pipeline.predict_proba(df_input)[0]
        end_time = time.perf_counter()
        latency_ms = round((end_time - start_time) * 1000, 2)

        estimated_score = float(probabilities[1])

        # 5. Determine Classification and Risk Tier
        if estimated_score >= threshold:
            classification = "Potentially Suspicious"
            risk_tier = "High"
        elif estimated_score >= (threshold * 0.70):
            classification = "Lower Model-Estimated Risk"
            risk_tier = "Medium"
        else:
            classification = "Lower Model-Estimated Risk"
            risk_tier = "Low"

        # 6. Generate local/global explainability details
        explanation = ModelExplainer.explain_prediction(
            pipeline=pipeline,
            raw_features=cleaned,
            estimated_score=estimated_score,
            classification=classification,
            top_k=5,
        )

        return {
            "estimated_score": round(estimated_score, 4),
            "classification": classification,
            "risk_tier": risk_tier,
            "decision_threshold": threshold,
            "model_version": metadata.get("version", "unknown"),
            "model_name": metadata.get("model_name", "Unknown-Model"),
            "algorithm_type": metadata.get("algorithm_type", "Unknown"),
            "explanation_summary": explanation["summary"],
            "feature_contributions": explanation["contributions"],
            "disclaimer": explanation["disclaimer"],
            "latency_ms": latency_ms,
            "cleaned_features": cleaned,
        }
