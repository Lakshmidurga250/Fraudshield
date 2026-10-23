from typing import Dict

import numpy as np
import pandas as pd

from ml.data.validator import EXPECTED_FEATURE_COLUMNS


class SyntheticDataGenerator:
    """Generates synthetic credit card transaction data strictly for testing and local UI development.

    NOTE: Synthetic data records are explicitly marked and must never be misrepresented
    as real Kaggle / ULB research dataset results.
    """

    @classmethod
    def generate_dataset(
        cls,
        n_normal: int = 1000,
        n_fraud: int = 50,
        random_seed: int = 42,
    ) -> pd.DataFrame:
        """Generate a synthetic DataFrame matching the Credit Card Fraud Detection research schema."""
        rng = np.random.default_rng(random_seed)

        # Normal transactions: V1-V28 are standard normal distributions centered around 0
        normal_v = rng.normal(loc=0.0, scale=1.0, size=(n_normal, 28))
        normal_amounts = np.abs(rng.exponential(scale=65.0, size=(n_normal, 1))) + 1.0
        normal_times = np.sort(rng.uniform(low=0.0, high=172800.0, size=(n_normal, 1)), axis=0)

        normal_data = np.hstack([normal_times, normal_v, normal_amounts])
        normal_labels = np.zeros((n_normal, 1))

        # Fraud transactions: specific PCA features show distinct shifted distributions
        # In Credit Card research data, V14, V12, V10, V4, V11 frequently show marked shifts
        fraud_v = rng.normal(loc=0.0, scale=1.5, size=(n_fraud, 28))
        fraud_v[:, 13] = rng.normal(loc=-6.5, scale=1.8, size=n_fraud)  # V14 strongly negative
        fraud_v[:, 11] = rng.normal(loc=-4.8, scale=1.6, size=n_fraud)  # V12 negative
        fraud_v[:, 9] = rng.normal(loc=-4.2, scale=1.5, size=n_fraud)  # V10 negative
        fraud_v[:, 3] = rng.normal(loc=4.5, scale=1.4, size=n_fraud)  # V4 positive
        fraud_v[:, 10] = rng.normal(loc=3.8, scale=1.2, size=n_fraud)  # V11 positive

        fraud_amounts = rng.choice([1.00, 29.99, 99.99, 450.00, 1200.00], size=(n_fraud, 1))
        fraud_times = rng.uniform(low=0.0, high=172800.0, size=(n_fraud, 1))

        fraud_data = np.hstack([fraud_times, fraud_v, fraud_amounts])
        fraud_labels = np.ones((n_fraud, 1))

        # Combine
        all_features = np.vstack([normal_data, fraud_data])
        all_labels = np.vstack([normal_labels, fraud_labels])

        # Permute rows
        shuffle_idx = rng.permutation(len(all_features))
        all_features = all_features[shuffle_idx]
        all_labels = all_labels[shuffle_idx]

        columns = EXPECTED_FEATURE_COLUMNS + ["Class"]
        combined = np.hstack([all_features, all_labels])

        df = pd.DataFrame(combined, columns=columns)
        df["Class"] = df["Class"].astype(int)
        return df

    @classmethod
    def get_sample_transaction(cls, profile: str = "normal") -> Dict[str, float]:
        """Return a pre-configured sample transaction dictionary for UI demo or quick testing."""
        features: Dict[str, float] = {"Time": 45000.0}

        if profile == "suspicious":
            # Distinctive fraud pattern based on benchmark research observations
            features["Amount"] = 890.50
            for i in range(1, 29):
                features[f"V{i}"] = 0.15
            features["V14"] = -6.20
            features["V12"] = -4.80
            features["V10"] = -3.90
            features["V4"] = 4.25
            features["V11"] = 3.60
            features["V17"] = -3.10
        else:
            # Low risk normal transaction
            features["Amount"] = 42.50
            for i in range(1, 29):
                features[f"V{i}"] = 0.05
            features["V14"] = 0.10
            features["V12"] = -0.15
            features["V4"] = -0.05

        return features
