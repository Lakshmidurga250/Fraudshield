from flask import Blueprint, Response, render_template, request
from flask_login import current_user, login_required

from database.models import TransactionAssessment
from extensions import db
from services.export_service import ExportService

history_bp = Blueprint("history", __name__)


@history_bp.route("/", methods=["GET"])
@history_bp.route("", methods=["GET"])
@login_required
def history_view():
    """Paginated, filterable transaction assessment audit table for current user."""
    page = request.args.get("page", 1, type=int)
    per_page = 10

    tier_filter = request.args.get("tier", "").strip()
    search_query = request.args.get("q", "").strip()
    sort_by = request.args.get("sort", "date_desc").strip()

    stmt = db.select(TransactionAssessment).filter_by(user_id=current_user.id)

    if tier_filter in ("Low", "Medium", "High"):
        stmt = stmt.filter(TransactionAssessment.risk_tier == tier_filter)

    if search_query:
        stmt = stmt.filter(TransactionAssessment.transaction_reference.ilike(f"%{search_query}%"))

    if sort_by == "score_desc":
        stmt = stmt.order_by(TransactionAssessment.estimated_score.desc())
    elif sort_by == "score_asc":
        stmt = stmt.order_by(TransactionAssessment.estimated_score.asc())
    elif sort_by == "date_asc":
        stmt = stmt.order_by(TransactionAssessment.created_at.asc())
    else:
        stmt = stmt.order_by(TransactionAssessment.created_at.desc())

    pagination = db.paginate(stmt, page=page, per_page=per_page, error_out=False)

    return render_template(
        "history/index.html",
        pagination=pagination,
        tier_filter=tier_filter,
        search_query=search_query,
        sort_by=sort_by,
    )


@history_bp.route("/export", methods=["GET"])
@login_required
def export_csv():
    """Download sanitized CSV of current user's assessment history."""
    csv_content = ExportService.export_user_assessments_csv(
        user_id=current_user.id, ip_address=request.remote_addr
    )
    filename = f"fraudshield_transactions_user_{current_user.id}.csv"
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
