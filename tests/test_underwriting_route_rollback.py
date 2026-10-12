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
from backend.app.schemas.credit_decision import CreditDecisionOutput
from backend.app.services.policy_version_service import policy_version_service
from backend.app.services.review_exception_service import (
    review_exception_service,
)
from backend.app.services.underwriting_pipeline import underwriting_pipeline
from backend.app.services.audit_log_service import audit_log_service


def test_underwriting_route_rolls_back_when_refer_workflow_fails(
    monkeypatch,
):
    suffix = uuid.uuid4().hex[:12].upper()
    application_id = f"ROLLBACK-{suffix}"
    customer_id = f"ROLLBACK-CUST-{suffix}"

    # Seed only the parent records. These are committed separately so the
    # request can exercise the actual foreign-key constraints.
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
                status="SUBMITTED",
            )
        )
        seed_db.commit()
    except Exception:
        seed_db.rollback()
        raise
    finally:
        seed_db.close()

    decision = CreditDecisionOutput(
        application_id=application_id,
        credit_score=742,
        risk_grade="B",
        probability_of_default=Decimal("0.01668"),
        affordability_score=Decimal("75"),
        repayment_propensity=Decimal("25"),
        fraud_score=Decimal("0"),
        income_stability_score=Decimal("80"),
        risk_segment="HIGH_RISK",
        recommended_amount=Decimal("150000"),
        recommended_tenure=12,
        recommended_emi=Decimal("13328.81"),
        foir=Decimal("38.5"),
        decision="REFER",
        confidence=Decimal("0.91"),
        reason_codes=[
            "WEAK_REPAYMENT_HISTORY",
            "POLICY_DATA_INCOMPLETE",
        ],
        model_version="SYNTHETIC-ROLLBACK-01",
        policy_version="POL-ROLLBACK-01",
        effective_from="2026-10-01T00:00:00",
    )

    captured_request_references = []
    original_audit_log = audit_log_service.log

    def capture_audit_log(**kwargs):
        captured_request_references.append(
            kwargs.get("request_reference")
        )
        return original_audit_log(**kwargs)

    monkeypatch.setattr(
        audit_log_service,
        "log",
        capture_audit_log,
    )

    def fake_policy_context(**kwargs):
        return {
            "policy_config": {},
            "policy_metadata": {
                "policy_version": "POL-ROLLBACK-01",
            },
        }

    def fake_pipeline_process(**kwargs):
        # The route consumes result.decision. A minimal result is sufficient
        # because the controlled failure happens before response construction.
        from types import SimpleNamespace

        return SimpleNamespace(decision=decision)

    def fail_exception_creation(**kwargs):
        raise RuntimeError("INJECTED_ROLLBACK_TEST_FAILURE")

    monkeypatch.setattr(
        policy_version_service,
        "get_policy_context",
        fake_policy_context,
    )
    monkeypatch.setattr(
        underwriting_pipeline,
        "process",
        fake_pipeline_process,
    )
    monkeypatch.setattr(
        review_exception_service,
        "create_exception",
        fail_exception_creation,
    )

    client = TestClient(app, raise_server_exceptions=False)

    try:
        response = client.post(
            "/underwriting/evaluate",
            json={
                "application": {
                    "application_id": application_id,
                    "customer_id": customer_id,
                    "requested_amount": "150000",
                    "loan_tenure_months": 12,
                },
                "borrower": {
                    "customer_id": customer_id,
                },
            },
        )

        assert response.status_code == 500, response.text

        payload = response.json()
        assert payload["success"] is False
        assert payload["error"]["code"] == "INTERNAL_SERVER_ERROR"

        request_id = response.headers.get("x-request-id")

        assert request_id is not None
        assert captured_request_references
        assert all(
            reference == request_id
            for reference in captured_request_references
        )

        # Verify using an independent database session.
        verify_db = SessionLocal()
        try:
            application = verify_db.get(
                LoanApplication,
                application_id,
            )
            assert application is not None
            assert application.status == "SUBMITTED"

            assert (
                verify_db.query(CreditDecision)
                .filter_by(application_id=application_id)
                .count()
                == 0
            )
            assert (
                verify_db.query(UnderwritingFeatureSnapshot)
                .filter_by(application_id=application_id)
                .count()
                == 0
            )
            assert (
                verify_db.query(DecisionTrace)
                .filter_by(application_id=application_id)
                .count()
                == 0
            )
            assert (
                verify_db.query(AuditLog)
                .filter_by(application_id=application_id)
                .count()
                == 0
            )
            assert (
                verify_db.query(ManualReview)
                .filter_by(application_id=application_id)
                .count()
                == 0
            )
            assert (
                verify_db.query(ReviewException)
                .filter_by(application_id=application_id)
                .count()
                == 0
            )
        finally:
            verify_db.close()

    finally:
        # Clean up any test records even if an assertion fails.
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