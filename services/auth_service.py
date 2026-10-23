from datetime import datetime, timezone
from typing import Optional, Tuple

from database.models import User
from extensions import db
from services.audit_service import AuditService


class AuthService:
    """Handles secure user registration, authentication verification, and session state."""

    @classmethod
    def register_user(
        cls,
        username: str,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[User]]:
        """Register a new user account with unique constraint validation and secure hashing."""
        username = username.strip()
        email = email.strip().lower()

        if len(username) < 3 or len(username) > 64:
            return False, "Username must be between 3 and 64 characters.", None

        if len(password) < 8:
            return False, "Password must be at least 8 characters in length.", None

        # Check existing username
        if db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none():
            return False, "Username is already registered.", None

        # Check existing email
        if db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none():
            return False, "Email address is already registered.", None

        try:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            AuditService.log(
                user_id=user.id,
                action="USER_REGISTRATION",
                ip_address=ip_address,
                details=f"User {username} registered successfully.",
            )
            return True, "Registration successful. You can now log in.", user
        except Exception as e:
            db.session.rollback()
            return False, f"Registration failed due to a database error: {str(e)}", None

    @classmethod
    def authenticate_user(
        cls,
        login_identifier: str,
        password: str,
        ip_address: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[User]]:
        """Authenticate user by either username or email with generic invalid credential response."""
        identifier = login_identifier.strip()
        if not identifier or not password:
            return False, "Invalid username/email or password.", None

        # Query by username or email
        user = db.session.execute(
            db.select(User).filter(
                (User.username == identifier) | (User.email == identifier.lower())
            )
        ).scalar_one_or_none()

        if not user or not user.check_password(password):
            AuditService.log(
                user_id=user.id if user else None,
                action="LOGIN_FAILURE",
                ip_address=ip_address,
                details=f"Failed login attempt for identifier: {identifier[:3]}***",
            )
            # Generic response to prevent account enumeration
            return False, "Invalid username/email or password.", None

        if not user.is_active:
            return False, "Account has been deactivated. Please contact support.", None

        user.last_login_at = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log(
            user_id=user.id,
            action="LOGIN_SUCCESS",
            ip_address=ip_address,
            details=f"User {user.username} authenticated successfully.",
        )
        return True, "Login successful.", user
