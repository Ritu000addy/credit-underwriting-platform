import uuid
from decimal import Decimal

from backend.app.database import SessionLocal

from backend.app.models.customer import Customer
from backend.app.models.loan_application import LoanApplication
from backend.app.models.audit_log import AuditLog
from backend.app.models.credit_decision import CreditDecision
from backend.app.models.decision_trace import DecisionTrace
from backend.app.models.underwriting_feature_snapshot import (
    UnderwritingFeatureSnapshot,
)
from backend.app.models.manual_review import ManualReview
from backend.app.models.review_exception import ReviewException

from backend.app.schemas.credit_decision import CreditDecisionOutput

from backend.app.services.audit_log_service import audit_log_service
from backend.app.services.credit_decision_service import credit_decision_service
from backend.app.services.decision_trace_service import decision_trace_service
from backend.app.services.manual_review_service import manual_review_service
from backend.app.services.review_exception_service import review_exception_service
from backend.app.services.underwriting_feature_snapshot_service import (
    underwriting_feature_snapshot_service,
)


def test_underwriting_related_records_rollback_together():
    application_id = f"ROLLBACK-{uuid.uuid4().hex[:12].upper()}"
    customer_id = f"ROLLBACK-CUST-{uuid.uuid4().hex[:12].upper()}"
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

    db = SessionLocal()
    verify_db = None

    # Create valid parent records in the same uncommitted transaction.
    db.add(
        Customer(
            customer_id=customer_id,
            kyc_status="PENDING",
        )
    )
    db.flush()

    db.add(
        LoanApplication(
            application_id=application_id,
            customer_id=customer_id,
            product="SYNTHETIC_TEST",
            requested_amount=Decimal("150000"),
            status="REFERRED",
        )
    )
    db.flush()

    try:
        saved_decision = credit_decision_service.save_decision(
            db=db,
            decision=decision,
            commit=False,
        )

        snapshot = underwriting_feature_snapshot_service.create_snapshot(
            db=db,
            application_id=application_id,
            decision_id=saved_decision.decision_id,
            model_version=decision.model_version,
            features={"synthetic_test": True},
        )

        trace = decision_trace_service.create_trace(
            db=db,
            application_id=application_id,
            decision_id=saved_decision.decision_id,
            feature_snapshot_id=snapshot.feature_snapshot_id,
            decision="REFER",
            model_version=decision.model_version,
            policy_version=decision.policy_version,
            effective_from=decision.effective_from,
            effective_to=decision.effective_to,
            model_outputs={"credit_score": 742},
            policy_evaluation=[],
            reason_codes=decision.reason_codes,
            decision_metadata={
                "feature_version": snapshot.feature_version,
            },
            commit=False,
        )

        decision_audit_id = f"AUDIT-{uuid.uuid4().hex[:12].upper()}"
        audit_log_service.log(
            db=db,
            audit_log_id=decision_audit_id,
            application_id=application_id,
            actor_type="SYSTEM",
            action="UNDERWRITING_DECISION",
            entity_type="CREDIT_DECISION",
            entity_reference=saved_decision.decision_id,
            description="Synthetic rollback integration test.",
            previous_state=None,
            new_state="REFER",
            request_reference="ROLLBACK-TEST",
            model_version=decision.model_version,
            policy_version=decision.policy_version,
        )

        review = manual_review_service.create_review(
            db=db,
            application_id=application_id,
            review_reason=", ".join(decision.reason_codes),
            commit=False,
        )

        exception = review_exception_service.create_exception(
            db=db,
            review_id=review.review_id,
            application_id=application_id,
            exception_type="UNDERWRITING_REFER",
            description="Synthetic rollback integration test.",
            created_by="SYSTEM",
        )

        exception_audit_id = f"AUDIT-{uuid.uuid4().hex[:12].upper()}"
        audit_log_service.log(
            db=db,
            audit_log_id=exception_audit_id,
            application_id=application_id,
            actor_type="SYSTEM",
            action="REVIEW_EXCEPTION_CREATED",
            entity_type="REVIEW_EXCEPTION",
            entity_reference=exception.exception_id,
            description="Synthetic rollback integration test.",
            previous_state=None,
            new_state="OPEN",
            request_reference="ROLLBACK-TEST",
            model_version=decision.model_version,
            policy_version=decision.policy_version,
        )

        # Confirm all records exist in the uncommitted transaction.
        assert db.get(CreditDecision, saved_decision.decision_id) is not None
        assert db.get(
            UnderwritingFeatureSnapshot, snapshot.feature_snapshot_id
        ) is not None
        assert db.get(DecisionTrace, trace.trace_id) is not None
        assert db.get(AuditLog, decision_audit_id) is not None
        assert db.get(ManualReview, review.review_id) is not None
        assert db.get(ReviewException, exception.exception_id) is not None
        assert db.get(AuditLog, exception_audit_id) is not None

        identifiers = {
            "decision": saved_decision.decision_id,
            "snapshot": snapshot.feature_snapshot_id,
            "trace": trace.trace_id,
            "decision_audit": decision_audit_id,
            "review": review.review_id,
            "exception": exception.exception_id,
            "exception_audit": exception_audit_id,
        }

        db.rollback()

    finally:
        # Ensure cleanup if an assertion or database operation fails.
        db.rollback()
        db.close()

    # Use an independent session to confirm the rollback persisted.
    verify_db = SessionLocal()
    try:
        assert verify_db.get(
            LoanApplication, application_id
        ) is None

        assert verify_db.get(
            Customer, customer_id
        ) is None
        assert verify_db.get(CreditDecision, identifiers["decision"]) is None
        assert verify_db.get(
            UnderwritingFeatureSnapshot, identifiers["snapshot"]
        ) is None
        assert verify_db.get(DecisionTrace, identifiers["trace"]) is None
        assert verify_db.get(AuditLog, identifiers["decision_audit"]) is None
        assert verify_db.get(ManualReview, identifiers["review"]) is None
        assert verify_db.get(
            ReviewException, identifiers["exception"]
        ) is None
        assert verify_db.get(
            AuditLog, identifiers["exception_audit"]
        ) is None
    finally:
        verify_db.close()