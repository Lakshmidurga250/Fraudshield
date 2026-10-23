from flask import Blueprint, jsonify, request
from flask_login import current_user

from ml.inference.predictor import FraudPredictor, ModelNotAvailableError
from ml.registry.metadata import ModelRegistry
from routes.api.schemas import validate_api_prediction_payload
from services.prediction_service import PredictionService

api_bp = Blueprint("api", __name__)


@api_bp.route("/health", methods=["GET"])
def api_health():
    """API health status endpoint."""
    active_meta = ModelRegistry.get_active_model_metadata()
    return jsonify(
        {
            "status": "healthy",
            "api_version": "v1",
            "active_model_registered": active_meta is not None,
        }
    ), 200


@api_bp.route("/models/active", methods=["GET"])
def get_active_model_api():
    """Retrieve verified active model metadata and evaluation metrics."""
    active_meta = ModelRegistry.get_active_model_metadata()
    if not active_meta:
        return jsonify({"status": "error", "message": "No active model registered."}), 404
    return jsonify({"status": "success", "data": active_meta}), 200


@api_bp.route("/predict", methods=["POST"])
def api_predict():
    """Inference API: evaluate risk score and explainability drivers for a transaction vector."""
    payload = request.get_json(silent=True)
    is_valid, errors, validated = validate_api_prediction_payload(payload)
    if not is_valid:
        return jsonify(
            {
                "status": "error",
                "message": "Validation failed.",
                "errors": errors,
            }
        ), 400

    features = validated["features"]
    threshold = validated["decision_threshold"]

    try:
        if current_user.is_authenticated:
            # Save to authenticated user's audit history
            assessment, result = PredictionService.assess_transaction(
                user_id=current_user.id,
                features=features,
                decision_threshold=threshold,
                ip_address=request.remote_addr,
            )
            result["transaction_reference"] = assessment.transaction_reference
        else:
            # Standalone API prediction without persistence
            result = FraudPredictor.predict(features, decision_threshold=threshold)

        return jsonify(
            {
                "status": "success",
                "data": result,
            }
        ), 200

    except ModelNotAvailableError as e:
        return jsonify(
            {
                "status": "error",
                "message": str(e),
            }
        ), 503
    except Exception as e:
        return jsonify(
            {
                "status": "error",
                "message": f"Inference failed: {str(e)}",
            }
        ), 500
