import datetime
from typing import Any, Dict, Tuple

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from ml.data.validator import EXPECTED_FEATURE_COLUMNS, DatasetValidator
from ml.evaluation.metrics import ModelEvaluator
from ml.preprocessing.pipeline import build_ml_pipeline
from ml.registry.metadata import ModelRegistry


class ModelTrainer:
    """Orchestrates reproducible training, evaluation, and artifact registration."""

    @classmethod
    def train(
        cls,
        df: pd.DataFrame,
        algorithm: str = "logistic_regression",
        test_size: float = 0.20,
        random_state: int = 42,
        decision_threshold: float = 0.50,
    ) -> Tuple[Any, Dict[str, Any]]:
        """Train pipeline, evaluate on held-out test split, and persist artifact.

        Returns (pipeline, metadata).
        """
        is_valid, errors, data_report = DatasetValidator.validate_training_dataframe(df)
        if not is_valid:
            raise ValueError(f"Training dataset validation failed: {'; '.join(errors)}")

        X = df[EXPECTED_FEATURE_COLUMNS]
        y = df["Class"].values.astype(int)

        # Held-out stratified train/test split BEFORE fitting any preprocessor
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, stratify=y, random_state=random_state
        )

        # Instantiate algorithm
        if algorithm.lower() in ("rf", "random_forest", "randomforest"):
            model_name = "RandomForest-Comparative"
            algorithm_type = "RandomForest"
            estimator = RandomForestClassifier(
                n_estimators=100,
                max_depth=12,
                class_weight="balanced_subsample",
                random_state=random_state,
                n_jobs=-1,
            )
        else:
            model_name = "LogisticRegression-Baseline"
            algorithm_type = "LogisticRegression"
            estimator = LogisticRegression(
                class_weight="balanced",
                max_iter=1000,
                solver="lbfgs",
                random_state=random_state,
            )

        # Build pipeline (Preprocessor + Classifier)
        pipeline = build_ml_pipeline(estimator)

        # Fit ONLY on training split
        pipeline.fit(X_train, y_train)

        # Predict probabilities on unseen test set
        y_test_proba = pipeline.predict_proba(X_test)[:, 1]

        # Evaluate performance
        eval_metrics = ModelEvaluator.evaluate(
            y_true=y_test,
            y_pred_proba=y_test_proba,
            decision_threshold=decision_threshold,
            training_samples=len(X_train),
            test_samples=len(X_test),
        )
        eval_metrics["algorithm"] = algorithm_type
        eval_metrics["dataset_origin"] = data_report.get("dataset_origin", "Local Dataset")
        eval_metrics["random_state"] = random_state

        # Generate version identifier
        timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        version = f"{algorithm_type.lower()}_{timestamp_str}"

        # Persist model artifact and metadata
        metadata = ModelRegistry.save_model_artifact(
            pipeline=pipeline,
            version=version,
            model_name=model_name,
            algorithm_type=algorithm_type,
            dataset_fingerprint=data_report["dataset_fingerprint"],
            metrics=eval_metrics,
            decision_threshold=decision_threshold,
        )

        return pipeline, metadata
