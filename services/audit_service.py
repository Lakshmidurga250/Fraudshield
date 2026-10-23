import logging
from typing import Optional

from database.models import AuditLog
from extensions import db

logger = logging.getLogger(__name__)


class AuditService:
    """Manages sensitive-data redacted operational and security audit logging."""

    @classmethod
    def log(
        cls,
        action: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[str] = None,
    ) -> None:
        try:
            # Redact common sensitive keywords from details string
            clean_details = details
            if clean_details:
                for sensitive in ["password", "token", "secret", "cvv", "card_number"]:
                    if sensitive in clean_details.lower():
                        clean_details = "[REDACTED SENSITIVE DATA]"
                        break

            entry = AuditLog(
                user_id=user_id,
                action=action,
                ip_address=ip_address,
                user_agent=user_agent[:250] if user_agent else None,
                details=clean_details,
            )
            db.session.add(entry)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.warning(f"Failed to record audit log: {e}")
