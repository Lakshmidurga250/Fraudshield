from typing import Any, Dict

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


class ModelEvaluator:
    """Computes comprehensive evaluation metrics for imbalanced fraud detection models."""

    @classmethod
    def evaluate(
        cls,
        y_true: np.ndarray,
        y_pred_proba: np.ndarray,
        decision_threshold: float = 0.50,
        training_samples: int = 0,
        test_samples: int = 0,
    ) -> Dict[str, Any]:
        """Compute all required metrics given true binary labels and positive class probabilities."""
        y_true = np.asarray(y_true).astype(int)
        y_pred_proba = np.asarray(y_pred_proba).astype(float)

        # Binary predictions based on threshold
        y_pred = (y_pred_proba >= decision_threshold).astype(int)

        # Confusion Matrix components
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        total_eval = len(y_true)

        # Scores
        precision = float(precision_score(y_true, y_pred, zero_division=0))
        recall = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))

        try:
            roc_auc = float(roc_auc_score(y_true, y_pred_proba))
        except ValueError:
            roc_auc = 0.5

        try:
            pr_auc = float(average_precision_score(y_true, y_pred_proba))
        except ValueError:
            pr_auc = 0.0

        # Sample points for ROC curve (downsampled to 25 points for efficient JSON serialization/Chart.js)
        fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
        roc_step = max(1, len(fpr) // 25)
        roc_points = [
            {"x": round(float(f), 4), "y": round(float(t), 4)}
            for f, t in zip(fpr[::roc_step], tpr[::roc_step], strict=False)
        ]
        if roc_points[-1]["x"] != 1.0 or roc_points[-1]["y"] != 1.0:
            roc_points.append({"x": 1.0, "y": 1.0})

        # Sample points for PR curve
        pr_precision, pr_recall, _ = precision_recall_curve(y_true, y_pred_proba)
        pr_step = max(1, len(pr_recall) // 25)
        pr_points = [
            {"x": round(float(r), 4), "y": round(float(p), 4)}
            for r, p in zip(pr_recall[::pr_step], pr_precision[::pr_step], strict=False)
        ]

        fraud_actual_count = int(np.sum(y_true == 1))
        non_fraud_actual_count = int(np.sum(y_true == 0))

        raw_accuracy = (tp + tn) / total_eval if total_eval > 0 else 0.0

        return {
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "raw_accuracy": round(raw_accuracy, 4),
            "decision_threshold": decision_threshold,
            "training_samples": training_samples,
            "test_samples": test_samples,
            "confusion_matrix": {
                "true_negatives": int(tn),
                "false_positives": int(fp),
                "false_negatives": int(fn),
                "true_positives": int(tp),
            },
            "class_distribution": {
                "actual_fraud": fraud_actual_count,
                "actual_non_fraud": non_fraud_actual_count,
                "predicted_fraud": int(tp + fp),
                "predicted_non_fraud": int(tn + fn),
            },
            "roc_curve_points": roc_points,
            "pr_curve_points": pr_points,
            "accuracy_warning": (
                "In highly imbalanced transaction datasets (e.g., ~0.17% fraud rate), a trivial model predicting "
                "always-non-fraud achieves 99.8% raw accuracy while missing 100% of frauds. PR-AUC, Recall, "
                "and Precision are the primary decision-grade evaluation metrics."
            ),
        }
