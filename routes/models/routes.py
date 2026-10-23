import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from ml.data.loader import DatasetLoader
from ml.registry.metadata import ModelRegistry
from ml.training.trainer import ModelTrainer

models_bp = Blueprint("models", __name__)


@models_bp.route("/", methods=["GET"])
@models_bp.route("", methods=["GET"])
@login_required
def models_view():
    """Model registry dashboard: shows active model, benchmarks, and training controls."""
    storage = ModelRegistry.get_storage_dir()
    all_models = []

    for meta_file in storage.glob("*.json"):
        if meta_file.name == "active_model.json":
            continue
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_models.append(data)
        except Exception:
            continue

    # Sort newest first
    all_models.sort(key=lambda x: x.get("version", ""), reverse=True)
    active_meta = ModelRegistry.get_active_model_metadata()

    # Check dataset availability
    loader = DatasetLoader()
    has_real_data = loader.has_real_dataset()

    return render_template(
        "models/index.html",
        models=all_models,
        active_model=active_meta,
        has_real_data=has_real_data,
    )


@models_bp.route("/train", methods=["POST"])
@login_required
def train_model_action():
    """Train a new baseline or comparative model and register artifact."""
    algorithm = request.form.get("algorithm", "logistic_regression")
    threshold = float(request.form.get("threshold", 0.50))
    use_synthetic = request.form.get("use_synthetic", "false").lower() == "true"

    loader = DatasetLoader()
    try:
        df, report = loader.load_dataset(prefer_real=not use_synthetic)
        pipeline, metadata = ModelTrainer.train(
            df=df,
            algorithm=algorithm,
            decision_threshold=threshold,
        )
        flash(
            f"Successfully trained {metadata['model_name']} (Version: {metadata['version']}). "
            f"PR-AUC: {metadata['metrics']['pr_auc']:.4f}, ROC-AUC: {metadata['metrics']['roc_auc']:.4f}",
            "success",
        )
    except Exception as e:
        flash(f"Model training failed: {str(e)}", "danger")

    return redirect(url_for("models.models_view"))


@models_bp.route("/activate/<version>", methods=["POST"])
@login_required
def activate_model_action(version: str):
    """Set specified model version as the active inference pipeline."""
    meta = ModelRegistry.get_model_metadata(version)
    if not meta:
        flash("Model version not found.", "danger")
        return redirect(url_for("models.models_view"))

    storage = ModelRegistry.get_storage_dir()
    pointer_path = storage / "active_model.json"
    with open(pointer_path, "w", encoding="utf-8") as f:
        json.dump({"active_version": version}, f, indent=2)

    flash(f"Model version '{version}' is now active.", "success")
    return redirect(url_for("models.models_view"))
