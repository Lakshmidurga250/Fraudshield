import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

import joblib


class ModelRegistry:
    """Secure registry for model artifacts, verification checksums, and version metadata."""

    @classmethod
    def get_storage_dir(cls) -> Path:
        base_dir = Path(__file__).resolve().parent.parent.parent
        storage = base_dir / "models" / "artifacts"
        storage.mkdir(parents=True, exist_ok=True)
        return storage

    @classmethod
    def calculate_sha256(cls, file_path: Path) -> str:
        """Calculate SHA-256 digest of a local artifact file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @classmethod
    def save_model_artifact(
        cls,
        pipeline: Any,
        version: str,
        model_name: str,
        algorithm_type: str,
        dataset_fingerprint: str,
        metrics: Dict[str, Any],
        decision_threshold: float = 0.50,
    ) -> Dict[str, Any]:
        """Save pipeline artifact and associated metadata JSON with cryptographic checksum."""
        storage = cls.get_storage_dir()
        artifact_filename = f"{version}.joblib"
        meta_filename = f"{version}.json"

        artifact_path = storage / artifact_filename
        meta_path = storage / meta_filename

        # Save model pipeline locally
        joblib.dump(pipeline, artifact_path, compress=3)

        # Calculate checksum
        sha256_digest = cls.calculate_sha256(artifact_path)

        metadata = {
            "version": version,
            "model_name": model_name,
            "algorithm_type": algorithm_type,
            "dataset_fingerprint": dataset_fingerprint,
            "decision_threshold": decision_threshold,
            "sha256_checksum": sha256_digest,
            "artifact_filename": artifact_filename,
            "metrics": metrics,
            "is_active": True,
        }

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        # Update active pointer
        active_pointer = storage / "active_model.json"
        with open(active_pointer, "w", encoding="utf-8") as f:
            json.dump({"active_version": version}, f, indent=2)

        return metadata

    @classmethod
    def get_active_model_metadata(cls) -> Optional[Dict[str, Any]]:
        """Return metadata for the currently active registered model."""
        storage = cls.get_storage_dir()
        pointer_path = storage / "active_model.json"
        if not pointer_path.exists():
            return None

        try:
            with open(pointer_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            active_version = data.get("active_version")
            if not active_version:
                return None
            return cls.get_model_metadata(active_version)
        except Exception:
            return None

    @classmethod
    def get_model_metadata(cls, version: str) -> Optional[Dict[str, Any]]:
        """Retrieve metadata JSON for a specific model version."""
        storage = cls.get_storage_dir()
        meta_path = storage / f"{version}.json"
        if not meta_path.exists():
            return None

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    @classmethod
    def load_active_model(cls) -> Optional[tuple[Any, Dict[str, Any]]]:
        """Load and verify active model pipeline.

        Returns (pipeline, metadata) or None if unavailable/corrupted.
        """
        meta = cls.get_active_model_metadata()
        if not meta:
            return None

        storage = cls.get_storage_dir()
        artifact_path = storage / meta["artifact_filename"]
        if not artifact_path.exists():
            return None

        # Verify cryptographic integrity
        current_checksum = cls.calculate_sha256(artifact_path)
        if current_checksum != meta["sha256_checksum"]:
            raise SecurityError(
                f"Model artifact checksum mismatch! Stored: {meta['sha256_checksum']}, Actual: {current_checksum}"
            )

        # Safe load from verified local artifact path
        pipeline = joblib.load(artifact_path)
        return pipeline, meta


class SecurityError(Exception):
    """Raised when an integrity check or authorization boundary is violated."""

    pass
