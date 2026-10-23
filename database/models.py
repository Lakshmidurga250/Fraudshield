import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db, login_manager


@login_manager.user_loader
def load_user(user_id: str) -> Optional["User"]:
    """Load user by primary key for Flask-Login."""
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None


class User(UserMixin, db.Model):
    """User account entity with secure password hashing and strict isolation."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    assessments = db.relationship(
        "TransactionAssessment",
        backref="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    audit_logs = db.relationship(
        "AuditLog",
        backref="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __init__(
        self,
        username: str,
        email: str,
        password_hash: Optional[str] = None,
        is_active: bool = True,
        is_admin: bool = False,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.username = username
        self.email = email
        if password_hash is not None:
            self.password_hash = password_hash
        self.is_active = is_active
        self.is_admin = is_admin

    def set_password(self, password: str) -> None:
        """Hash password using Werkzeug secure PBKDF2/scrypt implementation."""
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters in length.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify candidate password against securely stored hash."""
        if not self.password_hash or not password:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User id={self.id} username='{self.username}'>"


class TransactionAssessment(db.Model):
    """Per-user record of assessed transaction, model risk score, and explainability."""

    __tablename__ = "transaction_assessments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    transaction_reference = db.Column(db.String(64), unique=True, nullable=False, index=True)

    # Financial Transaction Features
    time_val = db.Column(db.Float, nullable=False, default=0.0)
    amount = db.Column(db.Float, nullable=False)

    # Anonymized PCA Features V1 through V28 stored in a structured JSON column
    # (Portable across SQLite, PostgreSQL, and other ORM targets)
    pca_features_json = db.Column(db.Text, nullable=False)

    # ML Inference Results
    estimated_score = db.Column(db.Float, nullable=False)  # Raw probability (0.0 - 1.0)
    decision_threshold = db.Column(db.Float, nullable=False, default=0.50)
    classification = db.Column(db.String(48), nullable=False)  # e.g. "Potentially Suspicious"
    risk_tier = db.Column(db.String(16), nullable=False)  # "Low", "Medium", "High"
    model_version = db.Column(db.String(64), nullable=False)
    model_name = db.Column(db.String(64), nullable=False)

    # Explainability Data
    explanation_summary = db.Column(db.Text, nullable=True)
    contributions_json = db.Column(
        db.Text, nullable=True
    )  # JSON list of {feature, contribution, direction}

    # Performance
    latency_ms = db.Column(db.Float, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    def __init__(
        self,
        user_id: int,
        transaction_reference: str,
        amount: float,
        estimated_score: float,
        classification: str,
        risk_tier: str,
        model_version: str,
        model_name: str,
        time_val: float = 0.0,
        decision_threshold: float = 0.50,
        pca_features_json: Optional[str] = None,
        pca_features: Optional[Dict[str, float]] = None,
        explanation_summary: Optional[str] = None,
        feature_contributions: Optional[List[Dict[str, Any]]] = None,
        latency_ms: Optional[float] = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.transaction_reference = transaction_reference
        self.amount = amount
        self.estimated_score = estimated_score
        self.classification = classification
        self.risk_tier = risk_tier
        self.model_version = model_version
        self.model_name = model_name
        self.time_val = time_val
        self.decision_threshold = decision_threshold
        if pca_features is not None:
            self.pca_features = pca_features
        elif pca_features_json is not None:
            self.pca_features_json = pca_features_json
        else:
            self.pca_features_json = "{}"
        if explanation_summary is not None:
            self.explanation_summary = explanation_summary
        if feature_contributions is not None:
            self.feature_contributions = feature_contributions
        if latency_ms is not None:
            self.latency_ms = latency_ms

    @property
    def pca_features(self) -> Dict[str, float]:
        """Deserialize PCA features V1-V28 from JSON."""
        try:
            return json.loads(self.pca_features_json)
        except (ValueError, TypeError):
            return {}

    @pca_features.setter
    def pca_features(self, data: Dict[str, float]) -> None:
        self.pca_features_json = json.dumps(data)

    @property
    def feature_contributions(self) -> List[Dict[str, Any]]:
        """Deserialize feature contributions list from JSON."""
        if not self.contributions_json:
            return []
        try:
            return json.loads(self.contributions_json)
        except (ValueError, TypeError):
            return []

    @feature_contributions.setter
    def feature_contributions(self, data: List[Dict[str, Any]]) -> None:
        self.contributions_json = json.dumps(data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert assessment to safe serialized dictionary."""
        return {
            "id": self.id,
            "transaction_reference": self.transaction_reference,
            "time_val": self.time_val,
            "amount": self.amount,
            "pca_features": self.pca_features,
            "estimated_score": round(self.estimated_score, 4),
            "decision_threshold": self.decision_threshold,
            "classification": self.classification,
            "risk_tier": self.risk_tier,
            "model_version": self.model_version,
            "model_name": self.model_name,
            "explanation_summary": self.explanation_summary,
            "feature_contributions": self.feature_contributions,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def sanitized_export_row(self) -> Dict[str, Any]:
        """Return safe, sanitized data row for CSV export (mitigates CSV formula injection)."""

        def sanitize_val(val: Any) -> Any:
            if isinstance(val, str) and val.startswith(("=", "+", "-", "@", "\t", "\r")):
                return f"'{val}"
            return val

        amt = self.amount if self.amount is not None else 0.0
        score = self.estimated_score if self.estimated_score is not None else 0.0
        thresh = self.decision_threshold if self.decision_threshold is not None else 0.50

        return {
            "Reference": sanitize_val(self.transaction_reference),
            "Timestamp": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
            "Amount": f"{amt:.2f}",
            "Estimated Risk Score": f"{score:.4f}",
            "Classification": sanitize_val(self.classification or ""),
            "Risk Tier": sanitize_val(self.risk_tier or ""),
            "Decision Threshold": f"{thresh:.2f}",
            "Model Name": sanitize_val(self.model_name or ""),
            "Model Version": sanitize_val(self.model_version or ""),
            "Summary": sanitize_val(self.explanation_summary or ""),
        }

    def __repr__(self) -> str:
        return f"<TransactionAssessment ref='{self.transaction_reference}' score={self.estimated_score:.4f}>"


class ModelMetadataRecord(db.Model):
    """Registry record tracking trained ML pipelines and verified evaluation metrics."""

    __tablename__ = "model_metadata_records"

    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(64), unique=True, nullable=False, index=True)
    model_name = db.Column(db.String(64), nullable=False)
    algorithm_type = db.Column(
        db.String(48), nullable=False
    )  # "LogisticRegression", "RandomForest"
    dataset_fingerprint = db.Column(db.String(64), nullable=False)
    is_active = db.Column(db.Boolean, default=False, nullable=False)

    # Sample Counts
    training_samples = db.Column(db.Integer, nullable=False)
    test_samples = db.Column(db.Integer, nullable=False)

    # Comprehensive Evaluation Metrics
    roc_auc = db.Column(db.Float, nullable=False)
    pr_auc = db.Column(db.Float, nullable=False)
    precision_val = db.Column(db.Float, nullable=False)
    recall_val = db.Column(db.Float, nullable=False)
    f1_val = db.Column(db.Float, nullable=False)
    decision_threshold = db.Column(db.Float, nullable=False, default=0.50)

    # Confusion matrix and detailed metrics
    metrics_json = db.Column(db.Text, nullable=False)

    # Artifact integrity
    artifact_path = db.Column(db.String(256), nullable=False)
    sha256_checksum = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __init__(
        self,
        version: str,
        model_name: str,
        algorithm_type: str,
        dataset_fingerprint: str,
        training_samples: int,
        test_samples: int,
        roc_auc: float,
        pr_auc: float,
        precision_val: float,
        recall_val: float,
        f1_val: float,
        metrics_json: str,
        artifact_path: str,
        sha256_checksum: str,
        decision_threshold: float = 0.50,
        is_active: bool = False,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.version = version
        self.model_name = model_name
        self.algorithm_type = algorithm_type
        self.dataset_fingerprint = dataset_fingerprint
        self.training_samples = training_samples
        self.test_samples = test_samples
        self.roc_auc = roc_auc
        self.pr_auc = pr_auc
        self.precision_val = precision_val
        self.recall_val = recall_val
        self.f1_val = f1_val
        self.metrics_json = metrics_json
        self.artifact_path = artifact_path
        self.sha256_checksum = sha256_checksum
        self.decision_threshold = decision_threshold
        self.is_active = is_active

    @property
    def metrics(self) -> Dict[str, Any]:
        try:
            return json.loads(self.metrics_json)
        except (ValueError, TypeError):
            return {}

    @metrics.setter
    def metrics(self, data: Dict[str, Any]) -> None:
        self.metrics_json = json.dumps(data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "model_name": self.model_name,
            "algorithm_type": self.algorithm_type,
            "dataset_fingerprint": self.dataset_fingerprint,
            "is_active": self.is_active,
            "training_samples": self.training_samples,
            "test_samples": self.test_samples,
            "roc_auc": round(self.roc_auc, 4),
            "pr_auc": round(self.pr_auc, 4),
            "precision": round(self.precision_val, 4),
            "recall": round(self.recall_val, 4),
            "f1_score": round(self.f1_val, 4),
            "decision_threshold": self.decision_threshold,
            "metrics": self.metrics,
            "artifact_path": self.artifact_path,
            "sha256_checksum": self.sha256_checksum,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditLog(db.Model):
    """Structured audit trail with sensitive data redaction."""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action = db.Column(db.String(64), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(256), nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    def __init__(
        self,
        action: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.action = action
        self.user_id = user_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "ip_address": self.ip_address,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
