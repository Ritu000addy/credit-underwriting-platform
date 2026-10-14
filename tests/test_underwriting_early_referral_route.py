import uuid
from decimal import Decimal

from fastapi.testclient import TestClient

from backend.app.database import SessionLocal
from backend.app.main import app
from backend.app.models.audit_log import AuditLog
from backend.app.models.credit_decision import CreditDecision
from backend.app.models.customer import Customer
from backend.app.models.decision_trace import DecisionTrace
from backend.app.models.loan_application import LoanApplication
from backend.app.models.manual_review import ManualReview
from backend.app.models.review_exception import ReviewException
from backend.app.models.underwriting_feature_snapshot import (
    UnderwritingFeatureSnapshot,
)
from backend.app.services.policy_version_service import (
    policy_version_service,
)


def test_early_evidence_referral_is_persisted(monkeypatch):
    suffix = uuid.uuid4().hex[:12].upper()
    application_id = f"EARLY-REFER-{suffix}"
    customer_id = f"EARLY-CUST-{suffix}"

    seed_db = SessionLocal()
    try:
        seed_db.add(
            Customer(
                customer_id=customer_id,
                kyc_status="PENDING",
            )
        )
        seed_db.flush()

        seed_db.add(
            LoanApplication(
                application_id=application_id,
                customer_id=customer_id,
                product="SYNTHETIC_TEST",
                requested_amount=Decimal("150000"),
                loan_tenure_months=12,
                annual_interest_rate=None,
                status="SUBMITTED",
            )
        )
        seed_db.commit()
    except Exception:
        seed_db.rollback()
        raise
    finally:
        seed_db.close()

    def fake_policy_context(**kwargs):
        return {
            "policy_config": {
                "kyc_bank_validation": {
                    "pan_required": True,
                    "ekyc_required": True,
                    "required_ekyc_result": "VERIFIED",
                    "aadhaar_kyc_required": False,
                },
            },
            "policy_metadata": {
                "policy_version": "POL-EARLY-REFER-TEST",
                "effective_from": "2026-10-01T00:00:00",
                "effective_to": None,
                "status": "ACTIVE",
            },
        }

    monkeypatch.setattr(
        policy_version_service,
        "get_policy_context",
        fake_policy_context,
    )

    try:
        client = TestClient(app, raise_server_exceptions=False)

        response = client.post(
            "/underwriting/evaluate",
            json={
                "application": {
                    "application_id": application_id,
                    "customer_id": customer_id,
                    "requested_amount": "150000",
                    "loan_tenure_months": 12,
                    "annual_interest_rate": None,
                },
                "borrower": {
                    "customer_id": customer_id,
                },
            },
        )

        assert response.status_code == 200, response.text

        payload = response.json()
        assert payload["success"] is True

        result = payload["data"]
        assert result["decision"]["decision"] == "REFER"
        assert result["risk_assessment"] is None
        assert result["policy"] is None
        assert (
            "APPLICATION_DATA_INCOMPLETE"
            in result["decision"]["reason_codes"]
        )

        verify_db = SessionLocal()
        try:
            application = verify_db.get(
                LoanApplication,
                application_id,
            )
            assert application.status == "REFERRED"

            decision = (
                verify_db.query(CreditDecision)
                .filter_by(application_id=application_id)
                .one()
            )
            assert decision.decision == "REFER"
            assert decision.credit_score is None
            assert decision.probability_of_default is None

            snapshot = (
                verify_db.query(UnderwritingFeatureSnapshot)
                .filter_by(application_id=application_id)
                .one()
            )
            assert snapshot.features == {}

            trace = (
                verify_db.query(DecisionTrace)
                .filter_by(application_id=application_id)
                .one()
            )
            assert trace.policy_evaluation == []
            assert (
                trace.decision_metadata["policy_evaluation_status"]
                == "NOT_EVALUATED"
            )

            review = (
                verify_db.query(ManualReview)
                .filter_by(application_id=application_id)
                .one()
            )
            assert review.review_status == "OPEN"

            exception = (
                verify_db.query(ReviewException)
                .filter_by(application_id=application_id)
                .one()
            )
            assert exception.status == "OPEN"

            audit_actions = {
                row.action
                for row in verify_db.query(AuditLog)
                .filter_by(application_id=application_id)
                .all()
            }
            assert "UNDERWRITING_DECISION" in audit_actions
            assert "RISK_ASSESSMENT_SKIPPED" in audit_actions
            assert "POLICY_EVALUATION_SKIPPED" in audit_actions
            assert "MANUAL_REVIEW_CREATED" in audit_actions
            assert "REVIEW_EXCEPTION_CREATED" in audit_actions

        finally:
            verify_db.close()

    finally:
        # Remove only records created for this synthetic test application.
        cleanup_db = SessionLocal()
        try:
            cleanup_db.query(ReviewException).filter_by(
                application_id=application_id
            ).delete(synchronize_session=False)

            cleanup_db.query(ManualReview).filter_by(
                application_id=application_id
            ).delete(synchronize_session=False)

            cleanup_db.query(DecisionTrace).filter_by(
                application_id=application_id
            ).delete(synchronize_session=False)

            cleanup_db.query(UnderwritingFeatureSnapshot).filter_by(
                application_id=application_id
            ).delete(synchronize_session=False)

            cleanup_db.query(AuditLog).filter_by(
                application_id=application_id
            ).delete(synchronize_session=False)

            cleanup_db.query(CreditDecision).filter_by(
                application_id=application_id
            ).delete(synchronize_session=False)

            cleanup_db.query(LoanApplication).filter_by(
                application_id=application_id
            ).delete(synchronize_session=False)

            cleanup_db.query(Customer).filter_by(
                customer_id=customer_id
            ).delete(synchronize_session=False)

            cleanup_db.commit()
        except Exception:
            cleanup_db.rollback()
            raise
        finally:
            cleanup_db.close()