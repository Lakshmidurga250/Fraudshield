from typing import Any

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler, StandardScaler


def build_preprocessor() -> ColumnTransformer:
    """Build preprocessing ColumnTransformer.

    - Amount & Time: Scaled with RobustScaler (robust to extreme financial outliers).
    - V1 through V28: Scaled with StandardScaler (centered PCA features).
    """
    scale_cols = ["Time", "Amount"]
    pca_cols = [f"V{i}" for i in range(1, 29)]

    preprocessor = ColumnTransformer(
        transformers=[
            ("robust_scaler", RobustScaler(), scale_cols),
            ("standard_scaler", StandardScaler(), pca_cols),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    return preprocessor


def build_ml_pipeline(estimator: Any) -> Pipeline:
    """Build full end-to-end Pipeline incorporating preprocessor and estimator.

    Ensures zero data leakage during cross-validation and evaluation.
    """
    preprocessor = build_preprocessor()
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", estimator),
        ]
    )
    return pipeline
