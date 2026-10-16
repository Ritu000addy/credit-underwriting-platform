
import importlib
import uuid
from decimal import Decimal

from fastapi.testclient import TestClient

from types import SimpleNamespace

from backend.app.core.security import get_current_user

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
from backend.app.models.manual_review_history import ManualReviewHistory

from backend.app.services.manual_review_history_service import (
    manual_review_history_service,
)


POLICY_VERSION = "POL-CHECKER-PERSISTENCE-TEST"
RECORD_SOURCE = "MANUAL_REVIEW_CHECKER"


def seed_checker_case():
    suffix = uuid.uuid4().hex[:12].upper()

    application_id = f"CHK-APP-{suffix}"
    customer_id = f"CHK-CUST-{suffix}"
    review_id = f"CHK-REV-{suffix}"
    original_decision_id = f"CHK-DEC-{suffix}"
    original_trace_id = f"CHK-TRACE-{suffix}"

    db = SessionLocal()

    try:
        db.add(
            Customer(
                customer_id=customer_id,
                kyc_status="VERIFIED",
            )
        )
        db.flush()

        db.add(
            LoanApplication(
                application_id=application_id,
                customer_id=customer_id,
                product="SYNTHETIC_TEST",
                requested_amount=Decimal("150000.00"),
                loan_tenure_months=12,
                annual_interest_rate=Decimal("12.00"),
                status="REFERRED",
            )
        )
        db.flush()

        db.add(
            CreditDecision(
                decision_id=original_decision_id,
                application_id=application_id,
                decision="REFER",
                reason_codes="UNDERWRITING_EVIDENCE_REVIEW_REQUIRED",
                policy_version=POLICY_VERSION,
                effective_from="2026-10-01T00:00:00",
                execution_environment="test",
                record_source="UNDERWRITING_WORKFLOW",
            )
        )
        db.flush()

        db.add(
            DecisionTrace(
                trace_id=original_trace_id,
                application_id=application_id,
                decision_id=original_decision_id,
                feature_snapshot_id=None,
                decision="REFER",
                model_version=None,
                policy_version=POLICY_VERSION,
                effective_from="2026-10-01T00:00:00",
                effective_to=None,
                model_outputs=None,
                policy_evaluation=None,
                reason_codes=[
                    "UNDERWRITING_EVIDENCE_REVIEW_REQUIRED"
                ],
                decision_metadata={
                    "policy_evaluation_status": "NOT_EVALUATED",
                },
            )
        )

        db.add(
            ManualReview(
                review_id=review_id,
                application_id=application_id,
                review_status="PENDING_CHECKER",
                review_reason="Synthetic persistence test",
                reviewer_id="maker.test",
                reviewer_decision="APPROVE",
                reviewer_remarks="Synthetic maker recommendation",
                maker_checker_required=True,
            )
        )

        db.commit()

        return {
            "application_id": application_id,
            "customer_id": customer_id,
            "review_id": review_id,
            "original_decision_id": original_decision_id,
            "original_trace_id": original_trace_id,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def cleanup_checker_case(case):
    db = SessionLocal()

    try:
        application_id = case["application_id"]

        db.query(AuditLog).filter(
            AuditLog.application_id == application_id
        ).delete(synchronize_session=False)

        db.query(ManualReviewHistory).filter(
            ManualReviewHistory.application_id == application_id
        ).delete(synchronize_session=False)

        db.query(ReviewException).filter(
            ReviewException.application_id == application_id
        ).delete(synchronize_session=False)

        db.query(DecisionTrace).filter(
            DecisionTrace.application_id == application_id
        ).delete(synchronize_session=False)

        db.query(UnderwritingFeatureSnapshot).filter(
            UnderwritingFeatureSnapshot.application_id == application_id
        ).delete(synchronize_session=False)

        db.query(CreditDecision).filter(
            CreditDecision.application_id == application_id
        ).delete(synchronize_session=False)

        db.query(ManualReview).filter(
            ManualReview.application_id == application_id
        ).delete(synchronize_session=False)

        db.query(LoanApplication).filter(
            LoanApplication.application_id == application_id
        ).delete(synchronize_session=False)

        db.query(Customer).filter(
            Customer.customer_id == case["customer_id"]
        ).delete(synchronize_session=False)

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def submit_checker_decision(
    application_id, 
    outcome,
    *,
    username="checker.test",
    role="CREDIT_OFFICER",
    submitted_checker_id=None,
):
    previous_override = app.dependency_overrides.get(get_current_user)

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        user_id="AUTH-CHECKER-TEST",
        username=username,
        role=role,
        is_active=True,
    )

    try:
        client = TestClient(app, raise_server_exceptions=False)

        return client.post(
            f"/manual-review/{application_id}/checker-decision",
            json={
                "checker_id": (
                    submitted_checker_id
                    if submitted_checker_id is not None
                    else username
                ),
                "checker_decision": outcome,
                "checker_remarks": "Synthetic checker persistence test",
            },
        )
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = previous_override


def test_checker_approval_preserves_original_refer_and_persists_final_trace():
    case = seed_checker_case()

    try:
        response = submit_checker_decision(
            case["application_id"],
            "APPROVE",
        )
        assert response.status_code == 200, response.text

        db = SessionLocal()
        try:
            original = db.get(
                CreditDecision,
                case["original_decision_id"],
            )

            assert original is not None
            assert original.decision == "REFER"
            assert original.record_source == "UNDERWRITING_WORKFLOW"

            final_decisions = (
                db.query(CreditDecision)
                .filter(
                    CreditDecision.application_id
                    == case["application_id"],
                    CreditDecision.record_source == RECORD_SOURCE,
                )
                .all()
            )

            assert len(final_decisions) == 1

            final_decision = final_decisions[0]
            assert final_decision.decision == "APPROVE"
            assert final_decision.policy_version == POLICY_VERSION
            assert "MANUAL_REVIEW_CHECKER_APPROVE" in (
                final_decision.reason_codes or ""
            )

            original_trace = db.get(
                DecisionTrace,
                case["original_trace_id"],
            )
            assert original_trace is not None
            assert original_trace.decision == "REFER"

            final_trace = (
                db.query(DecisionTrace)
                .filter(
                    DecisionTrace.decision_id
                    == final_decision.decision_id
                )
                .one()
            )

            assert final_trace.decision == "APPROVE"
            assert (
                final_trace.decision_metadata["original_decision_id"]
                == case["original_decision_id"]
            )
            assert (
                final_trace.decision_metadata["checker_decision"]
                == "APPROVE"
            )
            assert (
                final_trace.decision_metadata["policy_evaluation_status"]
                == "NOT_REEVALUATED"
            )

            application = db.get(
                LoanApplication,
                case["application_id"],
            )
            assert application.status == "APPROVED"

            review = db.get(ManualReview, case["review_id"])
            assert review.review_status == "COMPLETED"
            assert review.reviewer_id == "maker.test"
            assert review.checker_id == "checker.test"
            assert review.checker_decision == "APPROVE"

            history = manual_review_history_service.get_by_application(
                db=db,
                application_id=case["application_id"],
            )
            assert any(
                row.action == "CHECKER_DECISION"
                and row.new_status == "COMPLETED"
                for row in history
            )

            audit_rows = (
                db.query(AuditLog)
                .filter(
                    AuditLog.application_id
                    == case["application_id"]
                )
                .all()
            )

            final_audit = [
                row for row in audit_rows
                if row.action == "CREDIT_DECISION_CHECKER_FINALIZED"
            ]

            assert len(final_audit) == 1
            assert final_audit[0].previous_state == "REFER"
            assert final_audit[0].new_state == "APPROVE"
            assert (
                final_audit[0].entity_reference
                == final_decision.decision_id
            )

        finally:
            db.close()

    finally:
        cleanup_checker_case(case)


def test_checker_rejection_preserves_original_refer_and_persists_final_trace():
    case = seed_checker_case()

    try:
        response = submit_checker_decision(
            case["application_id"],
            "REJECT",
        )
        assert response.status_code == 200, response.text

        db = SessionLocal()
        try:
            original = db.get(
                CreditDecision,
                case["original_decision_id"],
            )

            assert original is not None
            assert original.decision == "REFER"

            final_decision = (
                db.query(CreditDecision)
                .filter(
                    CreditDecision.application_id
                    == case["application_id"],
                    CreditDecision.record_source == RECORD_SOURCE,
                )
                .one()
            )

            assert final_decision.decision == "REJECT"
            assert "MANUAL_REVIEW_CHECKER_REJECT" in (
                final_decision.reason_codes or ""
            )

            final_trace = (
                db.query(DecisionTrace)
                .filter(
                    DecisionTrace.decision_id
                    == final_decision.decision_id
                )
                .one()
            )

            assert final_trace.decision == "REJECT"
            assert (
                final_trace.decision_metadata["original_decision_id"]
                == case["original_decision_id"]
            )

            application = db.get(
                LoanApplication,
                case["application_id"],
            )
            assert application.status == "REJECTED"

            review = db.get(ManualReview, case["review_id"])
            assert review.review_status == "COMPLETED"
            assert review.checker_decision == "REJECT"

            final_audit = (
                db.query(AuditLog)
                .filter(
                    AuditLog.application_id
                    == case["application_id"],
                    AuditLog.action
                    == "CREDIT_DECISION_CHECKER_FINALIZED",
                )
                .one()
            )

            assert final_audit.previous_state == "REFER"
            assert final_audit.new_state == "REJECT"

        finally:
            db.close()

    finally:
        cleanup_checker_case(case)


def test_checker_failure_rolls_back_decision_trace_and_review_changes(
    monkeypatch,
):
    case = seed_checker_case()

    try:
        route_module = importlib.import_module(
            "backend.app.api.routes.manual_review"
        )

        def fail_history_record(*args, **kwargs):
            raise RuntimeError("SIMULATED_REVIEW_HISTORY_FAILURE")

        monkeypatch.setattr(
            route_module.manual_review_history_service,
            "record",
            fail_history_record,
        )

        response = submit_checker_decision(
            case["application_id"],
            "APPROVE",
        )

        assert response.status_code == 500

        db = SessionLocal()
        try:
            original = db.get(
                CreditDecision,
                case["original_decision_id"],
            )

            assert original is not None
            assert original.decision == "REFER"

            final_decisions = (
                db.query(CreditDecision)
                .filter(
                    CreditDecision.application_id
                    == case["application_id"],
                    CreditDecision.record_source == RECORD_SOURCE,
                )
                .all()
            )
            assert final_decisions == []

            traces = (
                db.query(DecisionTrace)
                .filter(
                    DecisionTrace.application_id
                    == case["application_id"]
                )
                .all()
            )
            assert len(traces) == 1
            assert traces[0].decision_id == case["original_decision_id"]
            assert traces[0].decision == "REFER"

            application = db.get(
                LoanApplication,
                case["application_id"],
            )
            assert application.status == "REFERRED"

            review = db.get(ManualReview, case["review_id"])
            assert review.review_status == "PENDING_CHECKER"
            assert review.checker_decision is None

            assert review.reviewer_id == "maker.test"
            assert review.reviewer_decision == "APPROVE"

            final_audits = (
                db.query(AuditLog)
                .filter(
                    AuditLog.application_id
                    == case["application_id"],
                    AuditLog.action
                    == "CREDIT_DECISION_CHECKER_FINALIZED",
                )
                .all()
            )
            assert final_audits == []

        finally:
            db.close()

    finally:
        cleanup_checker_case(case)


def test_checker_endpoint_rejects_unauthenticated_request():
    case = seed_checker_case()
    try:
        client = TestClient(app, raise_server_exceptions=False)

        response = client.post(
            f"/manual-review/{case['application_id']}/checker-decision",
            json={
                "checker_id": "checker.test",
                "checker_decision": "APPROVE",
            },
        )

        assert response.status_code == 401, response.text
    finally:
        cleanup_checker_case(case)


def test_checker_endpoint_rejects_insufficient_role():
    case = seed_checker_case()
    try:
        response = submit_checker_decision(
            case["application_id"],
            "APPROVE",
            role="OPERATIONS",
        )
        assert response.status_code == 403, response.text
    finally:
        cleanup_checker_case(case)


def test_checker_endpoint_rejects_forged_checker_identity():
    case = seed_checker_case()
    try:
        response = submit_checker_decision(
            case["application_id"],
            "APPROVE",
            username="checker.test",
            role="CREDIT_OFFICER",
            submitted_checker_id="someone.else",
        )

        assert response.status_code == 403, response.text

    finally:
        cleanup_checker_case(case)


def test_maker_cannot_approve_own_manual_review():
    case = seed_checker_case()

    try:
        response = submit_checker_decision(
            case["application_id"],
            "APPROVE",
            username="maker.test",
            submitted_checker_id="maker.test",
        )

        assert response.status_code == 403, response.text
        assert response.json()["error"]["code"] == "MAKER_CANNOT_BE_CHECKER"

    finally:
        cleanup_checker_case(case)