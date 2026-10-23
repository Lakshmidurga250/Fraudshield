"""CLI script for reproducible model pipeline training and registration."""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.data.loader import DatasetLoader
from ml.training.trainer import ModelTrainer


def main():
    parser = argparse.ArgumentParser(description="Train FraudShield ML Pipeline.")
    parser.add_argument(
        "--algorithm",
        type=str,
        default="logistic_regression",
        choices=["logistic_regression", "random_forest"],
        help="Algorithm architecture to train.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.50,
        help="Decision threshold for classification.",
    )
    parser.add_argument(
        "--force-synthetic",
        action="store_true",
        help="Force using the synthetic dataset even if real dataset exists.",
    )
    args = parser.parse_args()

    print(f"Loading dataset (prefer_real={not args.force_synthetic})...")
    loader = DatasetLoader()
    df, report = loader.load_dataset(prefer_real=not args.force_synthetic)
    print(f"Dataset Origin: {report.get('dataset_origin')}")
    print(
        f"Samples: {len(df)} total ({report.get('fraud_samples')} fraud, {report.get('non_fraud_samples')} normal)"
    )

    print(f"Training {args.algorithm} pipeline...")
    pipeline, metadata = ModelTrainer.train(
        df=df,
        algorithm=args.algorithm,
        decision_threshold=args.threshold,
    )

    print("\n--- Training Results ---")
    print(f"Model Name:         {metadata['model_name']}")
    print(f"Version:            {metadata['version']}")
    print(f"Algorithm Type:     {metadata['algorithm_type']}")
    print(f"PR-AUC:             {metadata['metrics']['pr_auc']:.4f}")
    print(f"ROC-AUC:            {metadata['metrics']['roc_auc']:.4f}")
    print(f"Precision:          {metadata['metrics']['precision']:.4f}")
    print(f"Recall:             {metadata['metrics']['recall']:.4f}")
    print(f"F1-Score:           {metadata['metrics']['f1_score']:.4f}")
    print(f"Raw Accuracy:       {metadata['metrics']['raw_accuracy']:.4f}")
    print(f"Artifact Checksum:  {metadata['sha256_checksum']}")
    print("\nPipeline successfully registered and marked active for inference.")


if __name__ == "__main__":
    main()
