from typing import Any, Dict

from sqlalchemy import func

from database.models import TransactionAssessment
from extensions import db
from ml.registry.metadata import ModelRegistry


class AnalyticsService:
    """Computes real-time analytics and chart datasets from database records and active model metadata."""

    @classmethod
    def get_user_dashboard_metrics(cls, user_id: int) -> Dict[str, Any]:
        """Aggregate metric cards, recent assessments, and chart series for user."""
        base_query = db.select(TransactionAssessment).filter_by(user_id=user_id)

        # Total counts
        total_count = (
            db.session.scalar(
                db.select(func.count(TransactionAssessment.id)).filter_by(user_id=user_id)
            )
            or 0
        )

        suspicious_count = (
            db.session.scalar(
                db.select(func.count(TransactionAssessment.id)).filter(
                    TransactionAssessment.user_id == user_id,
                    TransactionAssessment.classification == "Potentially Suspicious",
                )
            )
            or 0
        )

        low_risk_count = (
            db.session.scalar(
                db.select(func.count(TransactionAssessment.id)).filter(
                    TransactionAssessment.user_id == user_id,
                    TransactionAssessment.classification == "Lower Model-Estimated Risk",
                )
            )
            or 0
        )

        avg_score = db.session.scalar(
            db.select(func.avg(TransactionAssessment.estimated_score)).filter_by(user_id=user_id)
        )
        avg_score_val = round(float(avg_score), 4) if avg_score is not None else 0.0

        # Tier distribution counts
        high_tier_count = (
            db.session.scalar(
                db.select(func.count(TransactionAssessment.id)).filter(
                    TransactionAssessment.user_id == user_id,
                    TransactionAssessment.risk_tier == "High",
                )
            )
            or 0
        )

        med_tier_count = (
            db.session.scalar(
                db.select(func.count(TransactionAssessment.id)).filter(
                    TransactionAssessment.user_id == user_id,
                    TransactionAssessment.risk_tier == "Medium",
                )
            )
            or 0
        )

        low_tier_count = (
            db.session.scalar(
                db.select(func.count(TransactionAssessment.id)).filter(
                    TransactionAssessment.user_id == user_id,
                    TransactionAssessment.risk_tier == "Low",
                )
            )
            or 0
        )

        # Recent 10 assessments
        recent = (
            db.session.execute(
                base_query.order_by(TransactionAssessment.created_at.desc()).limit(10)
            )
            .scalars()
            .all()
        )

        # Chronological series for score timeline chart (last 20)
        timeline = (
            db.session.execute(
                base_query.order_by(TransactionAssessment.created_at.desc()).limit(20)
            )
            .scalars()
            .all()
        )
        timeline = list(reversed(timeline))

        timeline_labels = [t.transaction_reference.split("-")[-1] for t in timeline]
        timeline_scores = [round(t.estimated_score, 4) for t in timeline]
        timeline_thresholds = [round(t.decision_threshold, 2) for t in timeline]

        # Active model evaluation metadata
        active_meta = ModelRegistry.get_active_model_metadata()

        return {
            "total_assessments": total_count,
            "suspicious_assessments": suspicious_count,
            "low_risk_assessments": low_risk_count,
            "average_risk_score": avg_score_val,
            "risk_distribution": {
                "high": high_tier_count,
                "medium": med_tier_count,
                "low": low_tier_count,
            },
            "recent_assessments": recent,
            "timeline_chart": {
                "labels": timeline_labels,
                "scores": timeline_scores,
                "thresholds": timeline_thresholds,
            },
            "active_model": active_meta,
        }
