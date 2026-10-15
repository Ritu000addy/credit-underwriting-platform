
import uuid
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models.audit_log import AuditLog
from backend.app.models.credit_decision import CreditDecision
from backend.app.models.customer import Customer
from backend.app.models.loan_application import LoanApplication
from backend.app.models.sanction import Sanction
from backend.app.services.sanction_service import sanction_service


def test_sanction_and_audit_rollback_together(monkeypatch):
    suffix = uuid.uuid4().hex[:12].upper()
    customer_id = f"SANC-RB-CUST-{suffix}"
    application_id = f"SANC-RB-APP-{suffix}"
    decision_id = f"SANC-RB-DEC-{suffix}"
    sanction_id = f"SANC-RB-{suffix}"

    db = SessionLocal()
    verify_db = None

    try:
        # Create and commit the parent records and approved decision.
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

        db.add(
            CreditDecision(
                decision_id=decision_id,
                application_id=application_id,
                decision="APPROVE",
                recommended_amount=Decimal("150000.00"),
                recommended_tenure=12,
                recommended_emi=Decimal("13327.32"),
                policy_version="POL-SANCTION-RB-TEST",
                effective_from="2026-10-01T00:00:00",
                model_version="MODEL-SANCTION-RB-TEST",
            )
        )
        db.commit()

        # Fail the service's commit after it has added the sanction
        # and audit record. The original commit is not executed.
        def fail_commit():
            raise RuntimeError("INJECTED_SANCTION_COMMIT_FAILURE")

        monkeypatch.setattr(db, "commit", fail_commit)

        with pytest.raises(
            RuntimeError,
            match="INJECTED_SANCTION_COMMIT_FAILURE",
        ):
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
                terms_and_conditions="Synthetic rollback test",
            )

        # Roll back the uncommitted sanction and audit record.
        # Use the real Session.rollback method.
        Session.rollback(db)

    finally:
        Session.rollback(db)
        db.close()

    # Verify committed state from an independent session.
    verify_db = SessionLocal()
    try:
        assert verify_db.get(
            CreditDecision, decision_id
        ) is not None

        assert verify_db.get(
            Sanction, sanction_id
        ) is None

        audit_record = (
            verify_db.query(AuditLog)
            .filter(
                AuditLog.entity_reference == sanction_id,
                AuditLog.action == "SANCTION_CREATED",
            )
            .first()
        )
        assert audit_record is None

    finally:
        verify_db.close()

        # Remove the committed synthetic parent records.
        cleanup_db = SessionLocal()
        try:
            cleanup_db.query(CreditDecision).filter(
                CreditDecision.decision_id == decision_id
            ).delete(synchronize_session=False)

            cleanup_db.query(LoanApplication).filter(
                LoanApplication.application_id == application_id
            ).delete(synchronize_session=False)

            cleanup_db.query(Customer).filter(
                Customer.customer_id == customer_id
            ).delete(synchronize_session=False)

            cleanup_db.commit()
        except Exception:
            cleanup_db.rollback()
            raise
        finally:
            cleanup_db.close()
