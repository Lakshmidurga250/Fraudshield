import pytest

from app import create_app
from database.models import User
from extensions import db
from ml.data.synthetic import SyntheticDataGenerator
from ml.training.trainer import ModelTrainer


@pytest.fixture(scope="session")
def app():
    """Create application configured for testing."""
    application = create_app("testing")
    with application.app_context():
        db.create_all()

        # Train a deterministic baseline model for test suite
        df = SyntheticDataGenerator.generate_dataset(n_normal=200, n_fraud=20, random_seed=42)
        ModelTrainer.train(df=df, algorithm="logistic_regression", decision_threshold=0.50)

    yield application

    with application.app_context():
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Test client per test with clean session."""
    return app.test_client()


@pytest.fixture(scope="function")
def test_users(app):
    """Provide two distinct test users to verify cross-user isolation."""
    from database.models import TransactionAssessment, User
    with app.app_context():
        # Clear existing assessments and users for clean isolation tests
        db.session.query(TransactionAssessment).delete()
        db.session.query(User).delete()
        db.session.commit()

        user_a = User(username="alice", email="alice@example.com")
        user_a.set_password("Password123!")

        user_b = User(username="bob", email="bob@example.com")
        user_b.set_password("Password456!")

        db.session.add_all([user_a, user_b])
        db.session.commit()

        u_a_id = user_a.id
        u_b_id = user_b.id

    return {"user_a_id": u_a_id, "user_b_id": u_b_id}
