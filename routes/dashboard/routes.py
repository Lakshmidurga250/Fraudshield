from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from services.analytics_service import AnalyticsService

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    """Root entrypoint: route to dashboard if logged in, else to login."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard_view"))
    return redirect(url_for("auth.login"))


@dashboard_bp.route("/dashboard")
@login_required
def dashboard_view():
    """Main authenticated analytical dashboard."""
    metrics = AnalyticsService.get_user_dashboard_metrics(current_user.id)
    return render_template("dashboard/index.html", metrics=metrics)
