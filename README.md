# FraudShield — Machine Learning-Based Transaction Fraud Detection Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Flask 3.1](https://img.shields.io/badge/framework-Flask%203.1-black.svg)](https://flask.palletsprojects.com/)
[![scikit-learn](https://img.shields.io/badge/ML-scikit--learn-orange.svg)](https://scikit-learn.org/)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)]()
[![Coverage: 88%](https://img.shields.io/badge/coverage-88%25-brightgreen.svg)]()
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

> **Intelligent Transaction Risk Analysis. Explainable Machine Learning. Secure Analytics.**

FraudShield is a full-stack, modular, machine-learning-based web application that analyzes financial transaction feature vectors, estimates potential fraud risk probabilities, provides model-based directional explanations (XAI), and presents results through an interactive analytics dashboard.

Built specifically for software engineering excellence, portfolio presentation, academic evaluation, and production-minded ML practice.

---

## Key Highlights

- **Machine Learning Pipeline**: End-to-end `scikit-learn.pipeline.Pipeline` with `ColumnTransformer` (RobustScaler for heavy-tailed Amount/Time, StandardScaler for PCA features). Zero preprocessing data leakage.
- **Model Architectures**:
  - **Baseline**: Balanced-weight Logistic Regression with interpretable log-odds coefficients.
  - **Comparative**: Random Forest Classifier with ensemble tree depth pruning and Gini feature importances.
- **Explainable AI (XAI)**:
  - Local directional feature contributions ($x_i \cdot \beta_i$) showing exact features pushing transaction risk upward or downward.
  - Tree-based global feature weighting for ensemble models.
  - Transparent academic disclaimers: statistical contribution indicates model risk alignment, never ground-truth causation.
- **Security & Authorization**:
  - Secure password hashing using Werkzeug PBKDF2/scrypt.
  - Strict cross-user data isolation verified with integration and unit tests.
  - Anti-CSV formula injection neutralization.
  - CSRF protection across all forms and POST-only session logout.
  - Cryptographic SHA-256 model artifact integrity verification on every model load.
- **Visual Design System**: Tailored financial analytics palette (`#7865E8` primary purple, `#5546B8` dark purple, `#EEEAFF` lavender, `#F8F7FC` background), custom responsive CSS, and a zero-dependency offline Canvas charting engine.
- **Verifiable Quality**: 100% test pass rate across 26 unit, integration, and security tests with 88% branch and statement code coverage.

---

## Architecture Overview

```
                        ┌─────────────────────────────────────┐
                        │      Client Browser / REST API      │
                        └──────────────────┬──────────────────┘
                                           │ HTTPS / CSRF Token
                        ┌──────────────────▼──────────────────┐
                        │   Flask Application Factory (App)   │
                        │   (Blueprints: Auth, Dash, ML, API) │
                        └──────┬───────────────────────┬──────┘
                               │                       │
                ┌──────────────▼─────┐          ┌──────▼──────────────┐
                │  Service Layer     │          │  Database Layer     │
                │  - AuthService     │          │  - User             │
                │  - PredictService  │          │  - TransactionRecord│
                │  - AnalyticsService│          │  - ModelMetadata    │
                │  - ExportService   │          │  - AuditLog         │
                └──────────────┬─────┘          └─────────────────────┘
                               │
                ┌──────────────▼───────────────────────┐
                │        ML & Explainability Core      │
                │  - Preprocessing (ColumnTransformer) │
                │  - Logistic Regression / RF Model    │
                │  - Directional XAI Explainer         │
                │  - Cryptographic Artifact Registry   │
                └──────────────────────────────────────┘
```

---

## Getting Started on Windows

### 1. Prerequisites
- Windows 10/11 with PowerShell
- Python 3.11, 3.12, 3.13, or 3.14

### 2. Setup Virtual Environment

```powershell
# Clone or navigate to repository
cd c:\Users\lakshmi\OneDrive\Desktop\Fraudshield

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install -r requirements.txt
```

### 3. Initialize Database & Baseline ML Model

```powershell
# Generate deterministic synthetic benchmark sample dataset
python scripts/generate_synthetic_data.py

# Train and register baseline Logistic Regression pipeline
python scripts/train_model.py --algorithm logistic_regression

# (Optional) Train comparative Random Forest pipeline
python scripts/train_model.py --algorithm random_forest
```

### 4. Run the Development Server

```powershell
python app.py
```
Open your browser to: **`http://127.0.0.1:5000`**

---

## Dataset Instructions

FraudShield adheres to the schema of the public **Credit Card Fraud Detection** research dataset:
- **Columns**: `Time`, `V1` through `V28` (anonymized PCA features), `Amount`, and `Class` (0 = Normal, 1 = Fraud).

### Using the Full Research Dataset
1. Download `creditcard.csv` from Kaggle: [Credit Card Fraud Detection Dataset](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud).
2. Place the file inside the project directory at: `datasets/creditcard.csv`.
3. Retrain the model via CLI or web UI:
   ```powershell
   python scripts/train_model.py --algorithm logistic_regression
   ```
4. The system automatically detects the real dataset, validates the 31-column schema, fingerprints the data, and displays verification on the ML Registry dashboard.

---

## Testing & Quality Assurance

Run the complete test suite with coverage reporting:

```powershell
python -m pytest --cov=app --cov=database --cov=services --cov=ml --cov=routes --cov=config --cov-report=term-missing
```

Run code formatting and linting:

```powershell
python -m ruff check .
```

Measure verifiable lines of code:

```powershell
python scripts/measure_loc.py
```

Run latency benchmark (100 consecutive predictions):

```powershell
python benchmarks/latency_benchmark.py
```

---

## REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | System and active model health status |
| `/api/v1/health` | GET | REST API health check |
| `/api/v1/models/active` | GET | Active registered model metadata, fingerprint, and metrics |
| `/api/v1/predict` | POST | Assess fraud risk probability and directional drivers for a feature vector |

### Example API Prediction Request
```bash
curl -X POST http://127.0.0.1:5000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "decision_threshold": 0.50,
    "features": {
      "Time": 42000,
      "Amount": 890.50,
      "V1": 0.1, "V2": 0.1, "V3": 0.1, "V4": 4.25,
      "V5": 0.1, "V6": 0.1, "V7": 0.1, "V8": 0.1,
      "V9": 0.1, "V10": -3.9, "V11": 3.6, "V12": -4.8,
      "V13": 0.1, "V14": -6.2, "V15": 0.1, "V16": 0.1,
      "V17": -3.1, "V18": 0.1, "V19": 0.1, "V20": 0.1,
      "V21": 0.1, "V22": 0.1, "V23": 0.1, "V24": 0.1,
      "V25": 0.1, "V26": 0.1, "V27": 0.1, "V28": 0.1
    }
  }'
```

---

## Security Model & Limitations

- **Local Storage**: By default, SQLite is used at `instance/fraudshield.db`.
- **Cryptographic Trust**: Model artifacts (`.joblib`) are validated via SHA-256 digest checks against registered metadata JSON before loading.
- **Model Output Note**: Risk scores represent statistical classification probabilities derived from training distributions, not legal declarations of fraud.

---

## License

This software and associated materials are proprietary and confidential. All rights reserved.
