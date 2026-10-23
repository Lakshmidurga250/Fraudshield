from typing import Any, Dict, List, Tuple

from ml.data.validator import EXPECTED_FEATURE_COLUMNS


def validate_api_prediction_payload(data: Any) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Validate JSON payload received at /api/v1/predict."""
    errors = []
    if not isinstance(data, dict):
        return False, ["Payload must be a valid JSON object."], {}

    features = data.get("features")
    if not isinstance(features, dict):
        return False, ["Payload must include a 'features' dictionary."], {}

    # Check for required fields
    for col in EXPECTED_FEATURE_COLUMNS:
        if col not in features:
            errors.append(f"Missing required feature: '{col}'")
        else:
            try:
                val = float(features[col])
                if col == "Amount" and val < 0:
                    errors.append("Feature 'Amount' cannot be negative.")
            except (ValueError, TypeError):
                errors.append(f"Feature '{col}' must be a numeric value.")

    threshold = data.get("decision_threshold", 0.50)
    try:
        threshold = float(threshold)
        if not (0.01 <= threshold <= 0.99):
            errors.append("Field 'decision_threshold' must be between 0.01 and 0.99.")
    except (ValueError, TypeError):
        errors.append("Field 'decision_threshold' must be a valid float.")

    return len(errors) == 0, errors, {"features": features, "decision_threshold": threshold}
