from typing import Any, Dict, List

import pandas as pd

from ml.data.validator import EXPECTED_FEATURE_COLUMNS


class ModelExplainer:
    """Provides local directional feature contributions and global feature importances with transparent disclaimers."""

    DISCLAIMER: str = (
        "Statistical feature contribution and model probabilities represent mathematical risk associations "
        "and do not constitute proof of causation or definitive real-world fraud."
    )

    @classmethod
    def explain_prediction(
        cls,
        pipeline: Any,
        raw_features: Dict[str, float],
        estimated_score: float,
        classification: str,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """Generate local directional explanations for a single transaction prediction."""
        classifier = pipeline.named_steps.get("classifier")
        preprocessor = pipeline.named_steps.get("preprocessor")

        df_input = pd.DataFrame([raw_features])[EXPECTED_FEATURE_COLUMNS]

        # Check if model has linear coefficients (Logistic Regression)
        if hasattr(classifier, "coef_"):
            return cls._explain_logistic_regression(
                preprocessor=preprocessor,
                classifier=classifier,
                df_input=df_input,
                raw_features=raw_features,
                estimated_score=estimated_score,
                classification=classification,
                top_k=top_k,
            )

        # Check if tree-based with global feature importances (Random Forest)
        if hasattr(classifier, "feature_importances_"):
            return cls._explain_tree_model(
                classifier=classifier,
                raw_features=raw_features,
                estimated_score=estimated_score,
                classification=classification,
                top_k=top_k,
            )

        return {
            "explanation_type": "Unavailable",
            "summary": f"Prediction score {estimated_score:.4f} produced by {type(classifier).__name__}. Model-level explanation unavailable.",
            "contributions": [],
            "disclaimer": cls.DISCLAIMER,
        }

    @classmethod
    def _explain_logistic_regression(
        cls,
        preprocessor: Any,
        classifier: Any,
        df_input: pd.DataFrame,
        raw_features: Dict[str, float],
        estimated_score: float,
        classification: str,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """Compute exact directional log-odds feature contributions: transformed_x * coef."""
        # Get transformed feature values
        X_trans = preprocessor.transform(df_input)
        coefs = classifier.coef_[0]

        # Feature order from ColumnTransformer:
        # scale_cols = ["Time", "Amount"], pca_cols = ["V1" .. "V28"]
        transformed_names = ["Time", "Amount"] + [f"V{i}" for i in range(1, 29)]

        contributions: List[Dict[str, Any]] = []
        for name, val, coef in zip(transformed_names, X_trans[0], coefs, strict=False):
            contrib = float(val * coef)
            direction = "Risk Increasing" if contrib > 0 else "Risk Decreasing"
            contributions.append(
                {
                    "feature": name,
                    "raw_value": round(float(raw_features.get(name, 0.0)), 4),
                    "contribution": round(contrib, 4),
                    "direction": direction,
                    "magnitude": abs(contrib),
                }
            )

        # Sort by absolute impact
        contributions.sort(key=lambda item: item["magnitude"], reverse=True)
        top_contributions = contributions[:top_k]

        # Generate human-readable explanation summary
        top_drivers = [
            f"{c['feature']} ({c['direction']}, impact {c['contribution']:+.2f})"
            for c in top_contributions[:3]
        ]
        drivers_text = ", ".join(top_drivers) if top_drivers else "standard transaction attributes"

        summary = (
            f"Assessed as '{classification}' with model probability {estimated_score:.4f}. "
            f"Primary local directional drivers: {drivers_text}."
        )

        return {
            "explanation_type": "Local Directional Contribution (Logistic Regression)",
            "summary": summary,
            "contributions": top_contributions,
            "disclaimer": cls.DISCLAIMER,
        }

    @classmethod
    def _explain_tree_model(
        cls,
        classifier: Any,
        raw_features: Dict[str, float],
        estimated_score: float,
        classification: str,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """Provide global Gini feature importances for tree-based ensemble estimators."""
        importances = classifier.feature_importances_
        feature_names = ["Time", "Amount"] + [f"V{i}" for i in range(1, 29)]

        ranked: List[Dict[str, Any]] = []
        for name, imp in zip(feature_names, importances, strict=False):
            ranked.append(
                {
                    "feature": name,
                    "raw_value": round(float(raw_features.get(name, 0.0)), 4),
                    "global_importance": round(float(imp), 4),
                    "direction": "Global Feature Weight",
                    "magnitude": float(imp),
                }
            )

        ranked.sort(key=lambda item: item["magnitude"], reverse=True)
        top_ranked = ranked[:top_k]

        top_names = [f"{r['feature']} ({r['global_importance']:.1%})" for r in top_ranked[:3]]
        summary = (
            f"Assessed as '{classification}' with model probability {estimated_score:.4f}. "
            f"Top globally influential tree features: {', '.join(top_names)}."
        )

        return {
            "explanation_type": "Global Feature Importance (Random Forest)",
            "summary": summary,
            "contributions": top_ranked,
            "disclaimer": cls.DISCLAIMER,
        }
