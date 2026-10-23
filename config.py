import os
from pathlib import Path


class Config:
    """Base configuration with safe sensible defaults."""

    BASE_DIR = Path(__file__).resolve().parent
    INSTANCE_DIR = BASE_DIR / "instance"
    MODELS_DIR = BASE_DIR / "models" / "artifacts"
    DATASETS_DIR = BASE_DIR / "datasets"

    # Security: Secret Key
    SECRET_KEY = os.environ.get("SECRET_KEY", "fraudshield-dev-secret-key-change-in-production")

    # SQLAlchemy Database URI (defaults to SQLite in instance/)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{INSTANCE_DIR / 'fraudshield.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session & Cookie Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() in (
        "true",
        "1",
    )
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # ML & Risk Thresholds
    DEFAULT_DECISION_THRESHOLD = float(os.environ.get("DEFAULT_DECISION_THRESHOLD", 0.50))
    MIN_DECISION_THRESHOLD = 0.05
    MAX_DECISION_THRESHOLD = 0.95

    # File limits
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing environment configuration."""

    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False  # Allows straightforward form testing in unit tests
    SECRET_KEY = "test-secret-key-never-for-production"


class ProductionConfig(Config):
    """Production environment configuration with strict security enforcement."""

    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

    def __init__(self):
        super().__init__()
        secret = os.environ.get("SECRET_KEY")
        if not secret or secret == "fraudshield-dev-secret-key-change-in-production":
            raise ValueError(
                "Production environment requires a strong, explicit SECRET_KEY environment variable."
            )


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
