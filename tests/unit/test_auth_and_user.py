import pytest

from database.models import User
from services.auth_service import AuthService


def test_password_hashing(app):
    """Verify password hashing uses secure one-way hash and never stores plaintext."""
    with app.app_context():
        user = User(username="test_hasher", email="hasher@example.com")
        raw_pw = "SuperSecurePassword123!"
        user.set_password(raw_pw)

        assert user.password_hash != raw_pw
        assert len(user.password_hash) > 20
        assert user.check_password(raw_pw) is True
        assert user.check_password("WrongPassword") is False


def test_short_password_rejected(app):
    """Verify passwords under 8 characters are rejected."""
    with app.app_context():
        user = User(username="shorty", email="shorty@example.com")
        with pytest.raises(ValueError, match="at least 8 characters"):
            user.set_password("short")


def test_duplicate_registration_rejection(app):
    """Verify duplicate username and email are rejected gracefully."""
    with app.app_context():
        # First registration
        ok1, msg1, u1 = AuthService.register_user(
            username="dup_user",
            email="dup@example.com",
            password="ValidPassword123!",
        )
        assert ok1 is True
        assert u1 is not None

        # Duplicate username
        ok2, msg2, u2 = AuthService.register_user(
            username="dup_user",
            email="different@example.com",
            password="ValidPassword123!",
        )
        assert ok2 is False
        assert "Username is already registered" in msg2

        # Duplicate email
        ok3, msg3, u3 = AuthService.register_user(
            username="different_user",
            email="dup@example.com",
            password="ValidPassword123!",
        )
        assert ok3 is False
        assert "Email address is already registered" in msg3


def test_auth_generic_invalid_login(app):
    """Verify generic failure message when logging in with non-existent account or wrong password."""
    with app.app_context():
        ok, msg, user = AuthService.authenticate_user("nonexistent_user", "SomePassword123!")
        assert ok is False
        assert msg == "Invalid username/email or password."
        assert user is None
