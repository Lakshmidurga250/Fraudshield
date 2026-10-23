from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from routes.auth.forms import LoginForm, RegistrationForm
from services.audit_service import AuditService
from services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)


def is_safe_redirect_url(target: str) -> bool:
    """Ensure redirect destination is a relative local path to prevent open redirect vulnerabilities."""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(target)
    return test_url.scheme in ("", "http", "https") and (
        test_url.netloc == "" or test_url.netloc == ref_url.netloc
    )


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Register a new user account."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        ip_addr = request.remote_addr
        success, message, user = AuthService.register_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            ip_address=ip_addr,
        )
        if success and user:
            flash(message, "success")
            return redirect(url_for("auth.login"))
        else:
            flash(message, "danger")

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Sign into an existing user account."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        ip_addr = request.remote_addr
        success, message, user = AuthService.authenticate_user(
            login_identifier=form.identifier.data,
            password=form.password.data,
            ip_address=ip_addr,
        )
        if success and user:
            login_user(user, remember=form.remember_me.data)
            flash("Welcome back! Signed in successfully.", "success")
            next_page = request.args.get("next")
            if next_page and is_safe_redirect_url(next_page):
                return redirect(next_page)
            return redirect(url_for("dashboard.index"))
        else:
            flash(message, "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Sign out the current user session (strictly via POST)."""
    uid = current_user.id
    ip_addr = request.remote_addr
    logout_user()
    AuditService.log(
        user_id=uid,
        action="LOGOUT",
        ip_address=ip_addr,
        details="User logged out successfully.",
    )
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
