import logging
import os
from typing import Optional

from flask import Flask, jsonify, render_template, request
from flask_wtf.csrf import CSRFError

from config import config_by_name
from extensions import csrf, db, login_manager


def create_app(config_name: Optional[str] = None) -> Flask:
    """Application factory for FraudShield."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    config_class = config_by_name.get(config_name, config_by_name["default"])

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure critical directory paths exist
    os.makedirs(app.config["INSTANCE_DIR"], exist_ok=True)
    os.makedirs(app.config["MODELS_DIR"], exist_ok=True)
    os.makedirs(app.config["DATASETS_DIR"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configure structured logging with sensitive-data protection
    _configure_logging(app)

    # Register blueprints
    _register_blueprints(app)

    # Register error handlers
    _register_error_handlers(app)

    # Register core health & utility routes
    _register_core_routes(app)

    # Database initialization context
    with app.app_context():
        if app.config.get("TESTING", False):
            db.create_all()

    return app


def _configure_logging(app: Flask) -> None:
    """Configure secure structured logging."""
    log_format = "%(asctime)s [%(levelname)s] in %(module)s: %(message)s"
    logging.basicConfig(level=logging.INFO if not app.debug else logging.DEBUG, format=log_format)
    # Redact sensitive parameters from query logger if needed
    logging.getLogger("werkzeug").setLevel(logging.WARNING if not app.debug else logging.INFO)


def _register_blueprints(app: Flask) -> None:
    """Register all modular application blueprints."""
    from routes.api.routes import api_bp
    from routes.auth.routes import auth_bp
    from routes.dashboard.routes import dashboard_bp
    from routes.history.routes import history_bp
    from routes.models.routes import models_bp
    from routes.predictions.routes import predictions_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(predictions_bp, url_prefix="/predictions")
    app.register_blueprint(history_bp, url_prefix="/history")
    app.register_blueprint(api_bp, url_prefix="/api/v1")
    app.register_blueprint(models_bp, url_prefix="/models")

    # REST APIs accept direct JSON payloads from programmatic callers
    csrf.exempt(api_bp)


def _register_error_handlers(app: Flask) -> None:
    """Register centralized error handlers without leaking stack traces to clients."""

    @app.errorhandler(400)
    def bad_request_error(error):
        if request.path.startswith("/api/"):
            return jsonify(
                {"status": "error", "message": "Bad request.", "details": str(error)}
            ), 400
        return render_template("errors/400.html", error=error), 400

    @app.errorhandler(403)
    def forbidden_error(error):
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "message": "Access forbidden."}), 403
        return render_template("errors/403.html", error=error), 403

    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "message": "Requested resource not found."}), 404
        return render_template("errors/404.html", error=error), 404

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "message": "CSRF validation failed."}), 400
        return render_template(
            "errors/400.html",
            error="CSRF token expired or invalid. Please refresh the page and try again.",
        ), 400

    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.error(f"Internal Server Error: {error}", exc_info=True)
        if request.path.startswith("/api/"):
            return jsonify(
                {"status": "error", "message": "An internal server error occurred."}
            ), 500
        return render_template("errors/500.html"), 500


def _register_core_routes(app: Flask) -> None:
    """Register fundamental health and meta endpoints."""

    @app.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint reporting system, DB, and ML status."""
        db_healthy = False
        try:
            db.session.execute(db.text("SELECT 1"))
            db_healthy = True
        except Exception as e:
            app.logger.warning(f"Database health check failed: {e}")

        from ml.registry.metadata import ModelRegistry

        active_model = ModelRegistry.get_active_model_metadata()

        return jsonify(
            {
                "status": "healthy" if db_healthy else "degraded",
                "service": "FraudShield",
                "version": "1.0.0",
                "database_connected": db_healthy,
                "active_model_loaded": active_model is not None,
                "active_model_version": active_model.get("version") if active_model else None,
            }
        ), (200 if db_healthy else 503)


if __name__ == "__main__":
    application = create_app()
    with application.app_context():
        db.create_all()
    application.run(host="127.0.0.1", port=5000, debug=True)
