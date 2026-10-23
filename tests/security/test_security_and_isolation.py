from database.models import TransactionAssessment
from ml.data.synthetic import SyntheticDataGenerator
from services.export_service import ExportService
from services.prediction_service import PredictionService


def test_unauthenticated_routes_redirect_to_login(app):
    """Verify protected routes redirect unauthenticated users."""
    fresh_client = app.test_client()
    for path in ["/dashboard", "/predictions/new", "/history"]:
        resp = fresh_client.get(path, follow_redirects=False)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["Location"]


def test_cross_user_record_isolation(app, client, test_users):
    """Verify User A cannot access or view assessments belonging to User B."""
    u_b_id = test_users["user_b_id"]

    sample = SyntheticDataGenerator.get_sample_transaction("normal")

    with app.app_context():
        # User B creates an assessment
        assessment_b, _ = PredictionService.assess_transaction(
            user_id=u_b_id,
            features=sample,
        )
        ref_b = assessment_b.transaction_reference

    # Log in as User A
    with client:
        login_resp = client.post(
            "/auth/login",
            data={"identifier": "alice", "password": "Password123!"},
            follow_redirects=True,
        )
        assert login_resp.status_code == 200

        # User A tries to view User B's assessment detail -> must return 404 (or 403)
        detail_resp = client.get(f"/predictions/{ref_b}")
        assert detail_resp.status_code == 404

        # User A views their own history -> must NOT contain User B's transaction reference
        history_resp = client.get("/history")
        assert ref_b.encode("utf-8") not in history_resp.data


def test_csv_export_isolation_and_formula_sanitization(app, test_users):
    """Verify CSV export contains only the calling user's records and sanitizes potential formula injection."""
    u_a_id = test_users["user_a_id"]
    u_b_id = test_users["user_b_id"]

    sample = SyntheticDataGenerator.get_sample_transaction("normal")

    with app.app_context():
        from extensions import db
        db.session.query(TransactionAssessment).delete()
        db.session.commit()

        # User A assesses 1 transaction
        PredictionService.assess_transaction(user_id=u_a_id, features=sample)

        # User B assesses 1 transaction
        PredictionService.assess_transaction(user_id=u_b_id, features=sample)

        # Export User A's CSV
        csv_a = ExportService.export_user_assessments_csv(user_id=u_a_id)
        assert "Reference,Timestamp,Amount" in csv_a
        # Count non-header data rows
        data_rows = [
            line for line in csv_a.strip().split("\n") if line and not line.startswith("Reference")
        ]
        assert len(data_rows) == 1

        # Test CSV formula sanitization
        assessment = TransactionAssessment(
            user_id=u_a_id,
            transaction_reference="=SUM(A1:A10)",  # Malicious formula injection attempt
            amount=50.0,
            pca_features_json="{}",
            estimated_score=0.1,
            classification="Lower Model-Estimated Risk",
            risk_tier="Low",
            model_version="v1",
            model_name="test",
        )
        sanitized = assessment.sanitized_export_row()
        assert sanitized["Reference"].startswith("'=")  # Properly prefixed to neutralize in Excel
