import hashlib
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

EXPECTED_FEATURE_COLUMNS: List[str] = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]
EXPECTED_COLUMNS_WITH_TARGET: List[str] = EXPECTED_FEATURE_COLUMNS + ["Class"]


class DatasetValidator:
    """Validates schema, types, missing values, and statistical distributions of transaction data."""

    @staticmethod
    def calculate_dataset_fingerprint(df: pd.DataFrame) -> str:
        """Compute SHA-256 fingerprint from dataframe shape, columns, and sample hash."""
        summary = f"{df.shape}_{list(df.columns)}_{df.iloc[: min(50, len(df))].to_string()}"
        return hashlib.sha256(summary.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def validate_training_dataframe(
        cls, df: pd.DataFrame
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate dataframe intended for model training and evaluation.

        Returns (is_valid, errors, report).
        """
        errors: List[str] = []
        report: Dict[str, Any] = {}

        if df is None or not isinstance(df, pd.DataFrame):
            return False, ["Input is not a valid pandas DataFrame."], {}

        if df.empty:
            return False, ["DataFrame contains no rows."], {}

        # Check required columns
        missing_cols = [c for c in EXPECTED_COLUMNS_WITH_TARGET if c not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")

        # Check target column
        if "Class" in df.columns:
            unique_classes = set(df["Class"].dropna().unique())
            if not unique_classes.issubset({0, 1}):
                errors.append(
                    f"Target column 'Class' must contain only 0 and 1. Found: {unique_classes}"
                )

            class_counts = df["Class"].value_counts().to_dict()
            total_rows = len(df)
            fraud_count = int(class_counts.get(1, 0))
            non_fraud_count = int(class_counts.get(0, 0))
            fraud_ratio = fraud_count / total_rows if total_rows > 0 else 0.0

            report["total_samples"] = total_rows
            report["fraud_samples"] = fraud_count
            report["non_fraud_samples"] = non_fraud_count
            report["fraud_percentage"] = round(fraud_ratio * 100, 4)
            report["imbalance_ratio"] = (
                f"1:{round(non_fraud_count / fraud_count, 1)}" if fraud_count > 0 else "N/A"
            )

            if fraud_count < 2:
                errors.append(
                    "Dataset must contain at least 2 fraud-labelled samples for stratified splitting."
                )

        # Check missing values on existing feature columns
        existing_features = [c for c in EXPECTED_FEATURE_COLUMNS if c in df.columns]
        if existing_features:
            null_counts = df[existing_features].isnull().sum().to_dict()
            total_nulls = sum(null_counts.values())
            report["total_missing_values"] = int(total_nulls)
            if total_nulls > 0:
                cols_with_nulls = {k: v for k, v in null_counts.items() if v > 0}
                errors.append(f"Null values detected in feature columns: {cols_with_nulls}")

            # Check infinite / non-finite values
            numeric_df = df[existing_features].select_dtypes(include=[np.number])
            inf_mask = np.isinf(numeric_df.values).any(axis=1)
            inf_count = int(inf_mask.sum())
            report["infinite_values_count"] = inf_count
            if inf_count > 0:
                errors.append(
                    f"Detected {inf_count} rows containing non-finite or infinite values."
                )
        else:
            report["total_missing_values"] = 0
            report["infinite_values_count"] = 0

        report["dataset_fingerprint"] = cls.calculate_dataset_fingerprint(df)
        is_valid = len(errors) == 0
        return is_valid, errors, report

    @classmethod
    def validate_inference_features(
        cls, features: Dict[str, Any]
    ) -> Tuple[bool, List[str], Dict[str, float]]:
        """Validate a single transaction feature dictionary for inference.

        Returns (is_valid, errors, cleaned_numeric_features).
        """
        errors: List[str] = []
        cleaned: Dict[str, float] = {}

        if not isinstance(features, dict):
            return False, ["Features must be provided as a key-value dictionary."], {}

        for col in EXPECTED_FEATURE_COLUMNS:
            if col not in features:
                errors.append(f"Missing required feature: '{col}'")
                continue

            raw_val = features[col]
            if raw_val is None:
                errors.append(f"Feature '{col}' cannot be null.")
                continue

            try:
                numeric_val = float(raw_val)
            except (ValueError, TypeError):
                errors.append(f"Feature '{col}' must be a numeric value, received: {raw_val}")
                continue

            if np.isnan(numeric_val) or np.isinf(numeric_val):
                errors.append(f"Feature '{col}' must be a finite number.")
                continue

            # Financial domain validation on Amount
            if col == "Amount" and numeric_val < 0:
                errors.append("Transaction Amount cannot be negative.")

            cleaned[col] = numeric_val

        return (len(errors) == 0, errors, cleaned)
