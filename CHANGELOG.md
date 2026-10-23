# Changelog

All notable changes to the FraudShield project will be documented in this file.

## [1.0.0] - 2026-10-23

### Added
- **Application Factory**: Modular Flask architecture with centralized blueprints (`auth`, `dashboard`, `predictions`, `history`, `models`, `api`).
- **Authentication**: Secure registration, login (username/email), and POST logout with Werkzeug PBKDF2 password hashing.
- **Machine Learning**:
  - `scikit-learn.pipeline.Pipeline` with `ColumnTransformer` (RobustScaler for Amount/Time, StandardScaler for PCA features).
  - Logistic Regression baseline with balanced class weights.
  - Random Forest comparative classifier.
  - Evaluation engine calculating PR-AUC, ROC-AUC, Precision, Recall, F1-Score, and Confusion Matrix.
  - Cryptographically verified local model registry with SHA-256 integrity validation.
- **Explainable AI (XAI)**:
  - Local directional feature contribution analysis ($x_i \cdot \beta_i$).
  - Global Gini feature importance ranking for tree ensemble models.
  - Human-readable XAI synthesis summaries with academic disclaimers.
- **Frontend Dashboard**:
  - Semantic HTML5 and custom responsive CSS using `#7865E8` purple financial palette.
  - Standalone zero-dependency Canvas charting engine (`static/js/chart.min.js`) for risk distribution and score timeline series.
  - Accessible transaction assessment form with normal/suspicious quick presets.
  - Filterable, searchable, and paginated transaction history table.
  - Formula-sanitized CSV export for authenticated user records.
- **REST API**: Versioned endpoints (`/api/v1/predict`, `/api/v1/models/active`, `/api/v1/health`) with JSON schema validation.
- **Testing & Quality**: 26 automated unit, integration, and security tests achieving 88% statement coverage.
- **Tooling**: CLI scripts for data generation, training, LOC measurement, Git metrics, and latency benchmarking.
