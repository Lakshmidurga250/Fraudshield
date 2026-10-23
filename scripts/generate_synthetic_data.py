"""Script to generate a deterministic synthetic benchmark dataset for local development and testing."""

import argparse
from pathlib import Path

from ml.data.synthetic import SyntheticDataGenerator


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic transaction data.")
    parser.add_argument("--normal", type=int, default=1500, help="Number of normal transactions.")
    parser.add_argument("--fraud", type=int, default=75, help="Number of fraud transactions.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--output",
        type=str,
        default="datasets/sample/sample_creditcard.csv",
        help="Destination CSV file path.",
    )
    args = parser.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(
        f"Generating synthetic dataset: {args.normal} normal, {args.fraud} fraud (Seed: {args.seed})..."
    )
    df = SyntheticDataGenerator.generate_dataset(
        n_normal=args.normal, n_fraud=args.fraud, random_seed=args.seed
    )
    df.to_csv(out_path, index=False)
    print(f"Saved synthetic dataset to: {out_path} ({len(df)} total rows).")


if __name__ == "__main__":
    main()
