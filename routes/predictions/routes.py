from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from database.models import TransactionAssessment
from extensions import db
from ml.data.synthetic import SyntheticDataGenerator
from ml.inference.predictor import ModelNotAvailableError
from routes.predictions.forms import TransactionAssessmentForm
from services.prediction_service import PredictionService

predictions_bp = Blueprint("predictions", __name__)


@predictions_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_prediction():
    """Form and submission handler for new transaction assessments."""
    form = TransactionAssessmentForm()

    # Support pre-filling sample features for convenience/demo
    preset = request.args.get("preset")
    if request.method == "GET" and preset in ("normal", "suspicious"):
        sample = SyntheticDataGenerator.get_sample_transaction(profile=preset)
        form.amount.data = sample["Amount"]
        form.time_val.data = sample["Time"]
        for i in range(1, 29):
            getattr(form, f"v{i}").data = sample.get(f"V{i}", 0.0)

    if form.validate_on_submit():
        features = {
            "Amount": float(form.amount.data),
            "Time": float(form.time_val.data or 0.0),
        }
        for i in range(1, 29):
            val = getattr(form, f"v{i}").data
            features[f"V{i}"] = float(val if val is not None else 0.0)

        threshold = float(form.decision_threshold.data or 0.50)

        try:
            assessment, result = PredictionService.assess_transaction(
                user_id=current_user.id,
                features=features,
                decision_threshold=threshold,
                ip_address=request.remote_addr,
            )
            flash("Transaction assessed successfully.", "success")
            return redirect(
                url_for("predictions.view_assessment", reference=assessment.transaction_reference)
            )
        except ModelNotAvailableError as e:
            flash(str(e), "warning")
            return redirect(url_for("models.models_view"))
        except Exception as e:
            flash(f"Assessment error: {str(e)}", "danger")

    return render_template("predictions/new.html", form=form)


@predictions_bp.route("/<reference>", methods=["GET"])
@login_required
def view_assessment(reference: str):
    """View detailed assessment results, directional drivers, and threshold breakdown."""
    assessment = db.session.execute(
        db.select(TransactionAssessment).filter_by(
            transaction_reference=reference, user_id=current_user.id
        )
    ).scalar_one_or_none()

    if not assessment:
        # Cross-user isolation: return 404 if record doesn't belong to current user
        abort(404)

    return render_template("predictions/result.html", assessment=assessment)
