# REST API Reference

The FraudShield API exposes versioned endpoints under `/api/v1` for automated transaction risk evaluation and active model telemetry.

## Endpoints

### 1. Health Check
- **Route**: `GET /api/v1/health`
- **Response**:
```json
{
  "api_version": "v1",
  "status": "healthy",
  "active_model_registered": true
}
```

### 2. Active Model Metadata
- **Route**: `GET /api/v1/models/active`
- **Response**:
```json
{
  "status": "success",
  "data": {
    "version": "logisticregression_20261023_093410",
    "model_name": "LogisticRegression-Baseline",
    "algorithm_type": "LogisticRegression",
    "dataset_fingerprint": "a4b7f83e...",
    "decision_threshold": 0.50,
    "sha256_checksum": "60fb7921...",
    "metrics": {
      "pr_auc": 1.0000,
      "roc_auc": 1.0000,
      "precision": 1.0000,
      "recall": 0.9167,
      "f1_score": 0.9565
    }
  }
}
```

### 3. Evaluate Transaction Risk
- **Route**: `POST /api/v1/predict`
- **Content-Type**: `application/json`
- **Payload Schema**:
```json
{
  "decision_threshold": 0.50,
  "features": {
    "Time": 45000.0,
    "Amount": 120.00,
    "V1": 0.1, "V2": 0.05, "...": "...", "V28": 0.01
  }
}
```
- **Response**:
```json
{
  "status": "success",
  "data": {
    "estimated_score": 0.8842,
    "classification": "Potentially Suspicious",
    "risk_tier": "High",
    "decision_threshold": 0.50,
    "model_name": "LogisticRegression-Baseline",
    "model_version": "logisticregression_20261023_093410",
    "explanation_summary": "Assessed as 'Potentially Suspicious' with model probability 0.8842...",
    "feature_contributions": [
      {
        "feature": "V14",
        "raw_value": -6.2,
        "contribution": 1.84,
        "direction": "Risk Increasing"
      }
    ],
    "latency_ms": 2.45,
    "disclaimer": "Statistical feature contribution..."
  }
}
```
