import numpy as np
import pytest

from ml.data.synthetic import SyntheticDataGenerator
from ml.data.validator import DatasetValidator
from ml.inference.predictor import FraudPredictor
from ml.registry.metadata import ModelRegistry, SecurityError
from ml.training.trainer import ModelTrainer


def test_dataset_validator_success():
    """Verify clean synthetic dataset passes validation without errors."""
    df = SyntheticDataGenerator.generate_dataset(n_normal=100, n_fraud=10, random_seed=42)
    is_valid, errors, report = DatasetValidator.validate_training_dataframe(df)

    assert is_valid is True
    assert len(errors) == 0
    assert report["total_samples"] == 110
    assert report["fraud_samples"] == 10
    assert report["non_fraud_samples"] == 100


def test_dataset_validator_missing_column():
    """Verify validator flags missing column."""
    df = SyntheticDataGenerator.generate_dataset(n_normal=50, n_fraud=5, random_seed=42)
    df_missing = df.drop(columns=["V14"])
    is_valid, errors, _ = DatasetValidator.validate_training_dataframe(df_missing)

    assert is_valid is False
    assert any("V14" in err for err in errors)


def test_dataset_validator_invalid_labels():
    """Verify validator rejects non-binary labels."""
    df = SyntheticDataGenerator.generate_dataset(n_normal=50, n_fraud=5, random_seed=42)
    df.loc[0, "Class"] = 99
    is_valid, errors, _ = DatasetValidator.validate_training_dataframe(df)

    assert is_valid is False
    assert any("Target column 'Class' must contain only 0 and 1" in err for err in errors)


def test_dataset_validator_nan_and_inf():
    """Verify validator catches NaN or infinite values."""
    df = SyntheticDataGenerator.generate_dataset(n_normal=50, n_fraud=5, random_seed=42)
    df.loc[0, "Amount"] = np.nan
    is_valid, errors, _ = DatasetValidator.validate_training_dataframe(df)

    assert is_valid is False
    assert any("Null values detected" in err for err in errors)


def test_model_training_and_evaluation():
    """Verify end-to-end training, metrics calculation, and artifact registration."""
    df = SyntheticDataGenerator.generate_dataset(n_normal=300, n_fraud=30, random_seed=123)
    pipeline, metadata = ModelTrainer.train(
        df=df,
        algorithm="logistic_regression",
        decision_threshold=0.50,
    )

    assert metadata["model_name"] == "LogisticRegression-Baseline"
    assert "metrics" in metadata
    metrics = metadata["metrics"]
    assert 0.0 <= metrics["roc_auc"] <= 1.0
    assert 0.0 <= metrics["pr_auc"] <= 1.0
    assert "confusion_matrix" in metrics
    cm = metrics["confusion_matrix"]
    assert (
        cm["true_negatives"] + cm["false_positives"] + cm["false_negatives"] + cm["true_positives"]
        == metrics["test_samples"]
    )


def test_model_registry_integrity_check(tmp_path):
    """Verify tampering with a model artifact causes a SecurityError upon loading."""
    meta = ModelRegistry.get_active_model_metadata()
    assert meta is not None

    storage = ModelRegistry.get_storage_dir()
    artifact_path = storage / meta["artifact_filename"]
    assert artifact_path.exists()

    # Tamper with the artifact's metadata checksum
    meta_copy = dict(meta)
    meta_copy["sha256_checksum"] = "tampered_bad_checksum_hash"

    meta_file = storage / f"{meta['version']}.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        import json

        json.dump(meta_copy, f)

    with pytest.raises(SecurityError, match="checksum mismatch"):
        ModelRegistry.load_active_model()

    # Restore correct metadata
    with open(meta_file, "w", encoding="utf-8") as f:
        import json

        json.dump(meta, f)


def test_directional_explanation_generation():
    """Verify local directional explanations identify risk-increasing vs decreasing features."""
    sample = SyntheticDataGenerator.get_sample_transaction("suspicious")
    res = FraudPredictor.predict(sample)

    assert "estimated_score" in res
    assert "feature_contributions" in res
    assert len(res["feature_contributions"]) > 0

    contribs = res["feature_contributions"]
    # Verify top contributor structure
    top = contribs[0]
    assert "feature" in top
    assert "direction" in top
    assert top["direction"] in ("Risk Increasing", "Risk Decreasing", "Global Feature Weight")
    assert "disclaimer" in res
