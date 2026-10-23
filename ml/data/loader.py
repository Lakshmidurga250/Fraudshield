from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from ml.data.synthetic import SyntheticDataGenerator
from ml.data.validator import DatasetValidator


class DatasetLoader:
    """Manages dataset retrieval, schema validation, and origin tracking (Research vs Synthetic)."""

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            self.data_dir = Path(__file__).resolve().parent.parent.parent / "datasets"
        else:
            self.data_dir = Path(data_dir)
        self.sample_dir = self.data_dir / "sample"
        self.sample_dir.mkdir(parents=True, exist_ok=True)

    def get_real_dataset_path(self) -> Path:
        return self.data_dir / "creditcard.csv"

    def get_sample_dataset_path(self) -> Path:
        return self.sample_dir / "sample_creditcard.csv"

    def has_real_dataset(self) -> bool:
        path = self.get_real_dataset_path()
        return path.exists() and path.stat().st_size > 1000

    def ensure_sample_dataset(self) -> Path:
        """Create sample synthetic dataset if not already present on disk."""
        path = self.get_sample_dataset_path()
        if not path.exists():
            df = SyntheticDataGenerator.generate_dataset(n_normal=1200, n_fraud=60, random_seed=42)
            df.to_csv(path, index=False)
        return path

    def load_dataset(self, prefer_real: bool = True) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Load dataset and return (dataframe, metadata).

        Raises ValueError if dataset is corrupted or invalid.
        """
        real_path = self.get_real_dataset_path()
        if prefer_real and self.has_real_dataset():
            origin = "Research Dataset (creditcard.csv)"
            is_synthetic = False
            df = pd.read_csv(real_path)
        else:
            origin = "Synthetic Benchmark Sample (sample_creditcard.csv)"
            is_synthetic = True
            sample_path = self.ensure_sample_dataset()
            df = pd.read_csv(sample_path)

        is_valid, errors, report = DatasetValidator.validate_training_dataframe(df)
        if not is_valid:
            raise ValueError(f"Dataset validation failed: {'; '.join(errors)}")

        report["dataset_origin"] = origin
        report["is_synthetic"] = is_synthetic
        return df, report
