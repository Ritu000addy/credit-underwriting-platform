import uuid
from decimal import Decimal
from datetime import datetime

import pytest

from backend.app.database import SessionLocal
from backend.app.models.audit_log import AuditLog
from backend.app.models.credit_decision import CreditDecision
from backend.app.models.customer import Customer
from backend.app.models.loan_application import LoanApplication
from backend.app.models.sanction import Sanction
from backend.app.schemas.sanction import SanctionResponse
from backend.app.services.sanction_service import sanction_service


def create_test_records(decision_status: str):
    suffix = uuid.uuid4().hex[:12].upper()

    customer_id = f"SANC-LINK-CUST-{suffix}"
    application_id = f"SANC-LINK-APP-{suffix}"
    decision_id = f"SANC-LINK-DEC-{suffix}"
    sanction_id = f"SANC-LINK-{suffix}"

    db = SessionLocal()

    try:
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
                requested_amount=Decimal("150000.00"),
                status="APPROVED",
            )
        )
        db.flush()

        decision = CreditDecision(
            decision_id=decision_id,
            application_id=application_id,
            decision=decision_status,
            recommended_amount=Decimal("150000.00"),
            recommended_tenure=12,
            recommended_emi=Decimal("13327.32"),
            policy_version="POL-SANCTION-LINK-TEST",
            effective_from="2026-10-01T00:00:00",
            model_version="MODEL-SANCTION-LINK-TEST",
        )
        db.add(decision)
        db.commit()

        return (
            customer_id,
            application_id,
            decision_id,
            sanction_id,
        )

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def cleanup_test_records(
    customer_id: str,
    application_id: str,
    decision_id: str,
    sanction_id: str,
):
    db = SessionLocal()

    try:
        db.query(AuditLog).filter(
            AuditLog.entity_reference == sanction_id,
            AuditLog.action == "SANCTION_CREATED",
        ).delete(synchronize_session=False)

        db.query(Sanction).filter(
            Sanction.sanction_id == sanction_id
        ).delete(synchronize_session=False)

        db.query(CreditDecision).filter(
            CreditDecision.decision_id == decision_id
        ).delete(synchronize_session=False)

        db.query(LoanApplication).filter(
            LoanApplication.application_id == application_id
        ).delete(synchronize_session=False)

        db.query(Customer).filter(
            Customer.customer_id == customer_id
        ).delete(synchronize_session=False)

        db.commit()

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def test_sanction_persists_exact_approved_decision_id():
    (
        customer_id,
        application_id,
        decision_id,
        sanction_id,
    ) = create_test_records("APPROVE")

    try:
        db = SessionLocal()

        try:
            decision = db.get(CreditDecision, decision_id)
            assert decision is not None
            assert decision.decision == "APPROVE"

            sanction = sanction_service.create_sanction(
                db=db,
                sanction_id=sanction_id,
                application_id=application_id,
                sanctioned_amount=Decimal("150000.00"),
                sanctioned_tenure=12,
                sanctioned_emi=Decimal("13327.32"),
                interest_rate=Decimal("12.0000"),
                sanction_status="APPROVED",
                approval_authority="PYTEST",
                terms_and_conditions="Synthetic lineage test",
            )

            assert sanction.decision_id == decision.decision_id

        finally:
            db.close()

        # Verify persistence and API response mapping using a fresh session.
        verify_db = SessionLocal()

        try:
            persisted_sanction = verify_db.get(
                Sanction,
                sanction_id,
            )

            assert persisted_sanction is not None
            assert persisted_sanction.decision_id == decision_id

            response = SanctionResponse.model_validate(
                persisted_sanction
            )

            assert response.decision_id == decision_id
            assert response.application_id == application_id

        finally:
            verify_db.close()

    finally:
        cleanup_test_records(
            customer_id,
            application_id,
            decision_id,
            sanction_id,
        )


def test_non_approved_decision_cannot_authorize_sanction():
    (
        customer_id,
        application_id,
        decision_id,
        sanction_id,
    ) = create_test_records("REFER")

    try:
        db = SessionLocal()

        try:
            with pytest.raises(
                ValueError,
                match="APPLICATION_NOT_APPROVED: REFER",
            ):
                sanction_service.create_sanction(
                    db=db,
                    sanction_id=sanction_id,
                    application_id=application_id,
                    sanctioned_amount=Decimal("150000.00"),
                    sanctioned_tenure=12,
                    sanction_status="APPROVED",
                )

            db.rollback()

            assert db.get(Sanction, sanction_id) is None

        finally:
            db.close()

    finally:
        cleanup_test_records(
            customer_id,
            application_id,
            decision_id,
            sanction_id,
        )

def test_later_decision_does_not_change_existing_sanction_link():
    (
        customer_id,
        application_id,
        original_decision_id,
        sanction_id,
    ) = create_test_records("APPROVE")

    later_decision_id = (
        f"SANC-LINK-LATER-{uuid.uuid4().hex[:12].upper()}"
    )

    try:
        db = SessionLocal()

        try:
            original_decision = db.get(
                CreditDecision,
                original_decision_id,
            )
            assert original_decision is not None

            sanction_service.create_sanction(
                db=db,
                sanction_id=sanction_id,
                application_id=application_id,
                sanctioned_amount=Decimal("150000.00"),
                sanctioned_tenure=12,
                sanctioned_emi=Decimal("13327.32"),
                interest_rate=Decimal("12.0000"),
                sanction_status="APPROVED",
                approval_authority="PYTEST",
            )

            # Simulate a later underwriting decision for the same application.
            db.add(
                CreditDecision(
                    decision_id=later_decision_id,
                    application_id=application_id,
                    decision="REJECT",
                    policy_version="POL-SANCTION-LATER-TEST",
                    effective_from="2026-10-15T00:00:00",
                    model_version="MODEL-SANCTION-LATER-TEST",
                    created_at=datetime(2026, 10, 16, 12, 0, 0),
                )
            )
            db.commit()

        finally:
            db.close()

        # Verify using an independent database session.
        verify_db = SessionLocal()

        try:
            persisted_sanction = verify_db.get(
                Sanction,
                sanction_id,
            )

            assert persisted_sanction is not None
            assert persisted_sanction.decision_id == original_decision_id
            assert persisted_sanction.decision_id != later_decision_id

        finally:
            verify_db.close()

    finally:
        # Remove the later decision before cleaning up its application.
        cleanup_db = SessionLocal()

        try:
            cleanup_db.query(CreditDecision).filter(
                CreditDecision.decision_id == later_decision_id
            ).delete(synchronize_session=False)
            cleanup_db.commit()
        except Exception:
            cleanup_db.rollback()
            raise
        finally:
            cleanup_db.close()

        cleanup_test_records(
            customer_id,
            application_id,
            original_decision_id,
            sanction_id,
        )