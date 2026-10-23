# System Architecture Documentation

## Architectural Philosophy
FraudShield is structured following the **Layered Clean Architecture** and **Application Factory** pattern to enforce strict separation of concerns between web delivery, business domain logic, machine learning pipelines, and data persistence.

## Module Boundaries

1. **Presentation / Route Layer (`routes/`)**:
   - Manages HTTP input, form validation (Flask-WTF), CSRF validation, template rendering, and REST responses.
   - Delegates business workflows directly to `services/`.
   - Never directly fits ML estimators or manipulates raw joblib binaries.

2. **Service Layer (`services/`)**:
   - `AuthService`: User registration, PBKDF2 credential checking, and session lifecycle.
   - `PredictionService`: Coordinates model evaluation, assigns transaction reference IDs, and persists audit records.
   - `AnalyticsService`: Computes dashboard aggregates, risk distributions, and timeline chart series.
   - `ExportService`: Generates sanitized CSV files protected against formula injection.
   - `AuditService`: Records sensitive-data redacted operational logs.

3. **Machine Learning Layer (`ml/`)**:
   - `ml/data/`: Dataset schema validation, dataset fingerprinting, and synthetic benchmarking.
   - `ml/preprocessing/`: ColumnTransformer pipeline with RobustScaler for heavy-tailed Amount/Time and StandardScaler for PCA features.
   - `ml/training/`: Stratified split training for Logistic Regression baseline and Random Forest comparative model.
   - `ml/evaluation/`: Decision-grade metrics (PR-AUC, ROC-AUC, Precision, Recall, F1, Confusion Matrix).
   - `ml/explainability/`: Local directional feature contributions ($x_i \cdot \beta_i$) and global tree feature importances.
   - `ml/registry/`: Cryptographically verified model artifact loading with SHA-256 digest validation.

4. **Persistence Layer (`database/`)**:
   - SQLAlchemy ORM models (`User`, `TransactionAssessment`, `ModelMetadataRecord`, `AuditLog`).
   - Foreign key constraints with cascading deletes for strict multi-user privacy.
