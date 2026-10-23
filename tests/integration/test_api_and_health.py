from ml.data.synthetic import SyntheticDataGenerator


def test_system_health_endpoint(client):
    """Verify system health endpoint returns 200 and healthy status."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["service"] == "FraudShield"
    assert data["status"] == "healthy"
    assert data["database_connected"] is True
    assert data["active_model_loaded"] is True


def test_api_health_endpoint(client):
    """Verify /api/v1/health endpoint."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "healthy"
    assert data["api_version"] == "v1"


def test_api_get_active_model(client):
    """Verify /api/v1/models/active returns verified metadata and metrics."""
    resp = client.get("/api/v1/models/active")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert "metrics" in data["data"]
    assert "sha256_checksum" in data["data"]


def test_api_predict_success(client):
    """Verify valid JSON transaction vector receives valid probability assessment."""
    sample = SyntheticDataGenerator.get_sample_transaction("normal")
    payload = {
        "features": sample,
        "decision_threshold": 0.50,
    }
    resp = client.post("/api/v1/predict", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    res = data["data"]
    assert "estimated_score" in res
    assert 0.0 <= res["estimated_score"] <= 1.0
    assert res["classification"] in ("Potentially Suspicious", "Lower Model-Estimated Risk")
    assert res["risk_tier"] in ("Low", "Medium", "High")
    assert "feature_contributions" in res
    assert res["latency_ms"] >= 0.0


def test_api_predict_missing_feature(client):
    """Verify API rejects payload missing required feature with 400 Bad Request."""
    sample = SyntheticDataGenerator.get_sample_transaction("normal")
    del sample["V14"]  # Remove required feature
    payload = {"features": sample}

    resp = client.post("/api/v1/predict", json=payload)
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["status"] == "error"
    assert any("V14" in err for err in data["errors"])


def test_api_predict_negative_amount(client):
    """Verify API rejects negative transaction amount."""
    sample = SyntheticDataGenerator.get_sample_transaction("normal")
    sample["Amount"] = -10.0
    payload = {"features": sample}

    resp = client.post("/api/v1/predict", json=payload)
    assert resp.status_code == 400
    data = resp.get_json()
    assert any("Amount" in err for err in data["errors"])
