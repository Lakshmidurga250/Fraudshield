from ml.data.loader import DatasetLoader
from ml.data.synthetic import SyntheticDataGenerator
from ml.explainability.explainer import ModelExplainer
from ml.training.trainer import ModelTrainer


def test_dataset_loader(tmp_path):
    """Test DatasetLoader creating sample dataset and loading dataset."""
    loader = DatasetLoader(data_dir=tmp_path)
    assert loader.has_real_dataset() is False
    sample_path = loader.ensure_sample_dataset()
    assert sample_path.exists()
    assert sample_path.name == "sample_creditcard.csv"

    df, report = loader.load_dataset(prefer_real=False)
    assert len(df) > 0
    assert report["is_synthetic"] is True


def test_random_forest_training_and_tree_explanation():
    """Test Random Forest training and tree feature importance explainability."""
    df = SyntheticDataGenerator.generate_dataset(n_normal=100, n_fraud=15, random_seed=42)
    pipeline, meta = ModelTrainer.train(df=df, algorithm="random_forest")
    assert meta["algorithm_type"] == "RandomForest"

    sample = SyntheticDataGenerator.get_sample_transaction("suspicious")
    explanation = ModelExplainer.explain_prediction(
        pipeline=pipeline,
        raw_features=sample,
        estimated_score=0.88,
        classification="Potentially Suspicious",
    )
    assert "Global Feature Importance" in explanation["explanation_type"]
    assert len(explanation["contributions"]) > 0


def test_auth_views_workflow(client):
    """Test registration, login, safe redirect, and POST logout."""
    # Register new user
    reg_resp = client.post(
        "/auth/register",
        data={
            "username": "charlie",
            "email": "charlie@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
        follow_redirects=True,
    )
    assert reg_resp.status_code == 200
    assert b"Registration successful" in reg_resp.data

    # Log in
    login_resp = client.post(
        "/auth/login?next=/dashboard",
        data={"identifier": "charlie", "password": "Password123!"},
        follow_redirects=True,
    )
    assert login_resp.status_code == 200
    assert b"Transaction Risk Dashboard" in login_resp.data

    # Log out using POST
    logout_resp = client.post("/auth/logout", follow_redirects=True)
    assert logout_resp.status_code == 200
    assert b"You have been signed out" in logout_resp.data


def test_prediction_view_and_presets(client, test_users):
    """Test prediction form GET with preset and POST submission."""
    # Login as Alice
    client.post(
        "/auth/login",
        data={"identifier": "alice", "password": "Password123!"},
    )

    # Preset normal
    resp_preset = client.get("/predictions/new?preset=normal")
    assert resp_preset.status_code == 200

    # Submit valid form
    form_data = {
        "amount": "125.50",
        "time_val": "5000",
        "decision_threshold": "0.50",
    }
    for i in range(1, 29):
        form_data[f"v{i}"] = "0.05"
    form_data["v14"] = "-5.5"

    submit_resp = client.post("/predictions/new", data=form_data, follow_redirects=True)
    assert submit_resp.status_code == 200
    assert b"Assessment Details" in submit_resp.data
    assert b"TXN-" in submit_resp.data


def test_history_and_export_views(client, test_users):
    """Test history filtering and CSV export view."""
    client.post(
        "/auth/login",
        data={"identifier": "alice", "password": "Password123!"},
    )

    # Filter views
    r1 = client.get("/history?tier=High")
    assert r1.status_code == 200

    r2 = client.get("/history?sort=score_desc")
    assert r2.status_code == 200

    r3 = client.get("/history?q=TXN")
    assert r3.status_code == 200

    # CSV export
    exp_resp = client.get("/history/export")
    assert exp_resp.status_code == 200
    assert exp_resp.headers["Content-Type"].startswith("text/csv")
    assert b"Reference,Timestamp,Amount" in exp_resp.data


def test_models_view_and_activation(client, test_users):
    """Test models dashboard view, train trigger, and activation."""
    client.post(
        "/auth/login",
        data={"identifier": "alice", "password": "Password123!"},
    )

    resp = client.get("/models")
    assert resp.status_code == 200
    assert b"ML Model Registry" in resp.data

    # Train model action
    train_resp = client.post(
        "/models/train",
        data={"algorithm": "logistic_regression", "threshold": "0.50", "use_synthetic": "true"},
        follow_redirects=True,
    )
    assert train_resp.status_code == 200
    assert b"Successfully trained" in train_resp.data
