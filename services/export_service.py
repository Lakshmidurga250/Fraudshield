import csv
import io
from typing import Optional

from database.models import TransactionAssessment
from extensions import db
from services.audit_service import AuditService


class ExportService:
    """Provides secure, sanitized CSV generation for user transaction history."""

    @classmethod
    def export_user_assessments_csv(
        cls,
        user_id: int,
        ip_address: Optional[str] = None,
    ) -> str:
        """Export only the specified user's assessments as formula-sanitized CSV."""
        assessments = (
            db.session.execute(
                db.select(TransactionAssessment)
                .filter_by(user_id=user_id)
                .order_by(TransactionAssessment.created_at.desc())
            )
            .scalars()
            .all()
        )

        output = io.StringIO()
        fieldnames = [
            "Reference",
            "Timestamp",
            "Amount",
            "Estimated Risk Score",
            "Classification",
            "Risk Tier",
            "Decision Threshold",
            "Model Name",
            "Model Version",
            "Summary",
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        for a in assessments:
            writer.writerow(a.sanitized_export_row())

        AuditService.log(
            user_id=user_id,
            action="CSV_EXPORTED",
            ip_address=ip_address,
            details=f"Exported {len(assessments)} transaction records.",
        )

        return output.getvalue()
