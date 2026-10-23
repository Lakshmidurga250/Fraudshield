import datetime
import secrets
from typing import Any, Dict, Optional, Tuple

from database.models import TransactionAssessment
from extensions import db
from ml.inference.predictor import FraudPredictor
from services.audit_service import AuditService


class PredictionService:
    """Coordinates risk inference, data persistence, and transaction audit trails."""

    @classmethod
    def generate_transaction_reference(cls) -> str:
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
        rand_token = secrets.token_hex(4).upper()
        return f"TXN-{date_str}-{rand_token}"

    @classmethod
    def assess_transaction(
        cls,
        user_id: int,
        features: Dict[str, Any],
        decision_threshold: Optional[float] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[TransactionAssessment, Dict[str, Any]]:
        """Run ML assessment and record transaction in user's isolated history."""
        # Run inference
        result = FraudPredictor.predict(features, decision_threshold=decision_threshold)
        cleaned = result["cleaned_features"]

        pca_dict = {f"V{i}": cleaned[f"V{i}"] for i in range(1, 29)}
        txn_ref = cls.generate_transaction_reference()

        assessment = TransactionAssessment(
            user_id=user_id,
            transaction_reference=txn_ref,
            time_val=cleaned["Time"],
            amount=cleaned["Amount"],
            pca_features=pca_dict,
            estimated_score=result["estimated_score"],
            decision_threshold=result["decision_threshold"],
            classification=result["classification"],
            risk_tier=result["risk_tier"],
            model_version=result["model_version"],
            model_name=result["model_name"],
            explanation_summary=result["explanation_summary"],
            feature_contributions=result["feature_contributions"],
            latency_ms=result["latency_ms"],
        )

        db.session.add(assessment)
        db.session.commit()

        AuditService.log(
            user_id=user_id,
            action="TRANSACTION_ASSESSED",
            ip_address=ip_address,
            details=f"Assessed {txn_ref} - Score: {result['estimated_score']:.4f} ({result['classification']})",
        )

        return assessment, result
