# Machine Learning Methodology & Evaluation Protocol

## 1. Research Dataset Schema
FraudShield models data structured identically to the public **Credit Card Fraud Detection** research benchmark (ULB / Kaggle):
- `Time`: Elapsed seconds from first recording.
- `V1`–`V28`: Principal Component Analysis (PCA) transformed features preserving transaction privacy.
- `Amount`: Raw transaction currency value (heavy-tailed, right-skewed).
- `Class`: Ground-truth label where `1` = Fraudulent, `0` = Genuine.

## 2. Preprocessing & Leakage Safeguards
Data leakage is prevented by encapsulating transformations strictly inside an `sklearn.pipeline.Pipeline`:
- Scalers and transformers are fitted **strictly on training partitions**.
- **Amount & Time**: Scaled with `RobustScaler` (using median and interquartile range), ensuring robust normalization in the presence of extreme financial outliers.
- **V1–V28**: Scaled with `StandardScaler` (zero mean, unit variance).

## 3. Estimator Architectures
1. **Logistic Regression (Baseline)**:
   - Hyperparameters: `class_weight='balanced'`, `max_iter=1000`, `solver='lbfgs'`.
   - Balanced weights compensate for extreme class imbalance (~0.17% fraud in natural datasets).
   - Linear formulation enables exact local directional explainability.
2. **Random Forest (Comparative)**:
   - Hyperparameters: `n_estimators=100`, `max_depth=12`, `class_weight='balanced_subsample'`.
   - Captures non-linear feature interactions with controlled tree depth.

## 4. Evaluation Philosophy: Why Accuracy Fails
In highly imbalanced datasets, a trivial model predicting universal non-fraud scores 99.8% raw accuracy while missing 100% of frauds.
FraudShield uses:
- **PR-AUC (Average Precision)**: Primary metric summarizing precision across all decision thresholds.
- **ROC-AUC**: Evaluates ranking capability between positive and negative distributions.
- **Recall (Sensitivity)**: Fraction of actual frauds successfully identified.
- **Precision**: Fraction of flagged transactions that are actually fraudulent.

## 5. Explainable AI (XAI)
- **Local Directional Contributions**: Calculated as transformed feature value multiplied by logistic regression coefficient ($x_i \cdot \beta_i$). Features with positive contributions push model probability higher toward suspicious classification; features with negative contributions push it toward normal.
- **Causation Disclaimer**: Statistical contribution coefficients quantify model correlation alignment and do not prove real-world causality.
