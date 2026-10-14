import uuid
from datetime import datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from backend.app.database import SessionLocal
from backend.app.main import app
from backend.app.models.audit_log import AuditLog
from backend.app.models.customer import Customer
from backend.app.models.disbursement import Disbursement
from backend.app.models.internal_ledger import InternalLedger
from backend.app.models.loan_application import LoanApplication
from backend.app.models.reconciliation import Reconciliation


def seed_processed_disbursement():
    suffix = uuid.uuid4().hex[:12].upper()
    application_id = f"WEBHOOK-APP-{suffix}"
    customer_id = f"WEBHOOK-CUST-{suffix}"
    disbursement_id = f"WEBHOOK-DISB-{suffix}"

    bank_reference = f"WEBHOOK-BANK-REF-{suffix}"
    amount = Decimal("1000.00")
    now = datetime.utcnow()

    case = {
        "application_id": application_id,
        "customer_id": customer_id,
        "disbursement_id": disbursement_id,
        "bank_reference": bank_reference,
        "amount": amount,
    }

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
                product="SYNTHETIC_WEBHOOK_TEST",
                requested_amount=Decimal("1000.00"),
                loan_tenure_months=12,
                annual_interest_rate=Decimal("12.00"),
                status="APPROVED",
            )
        )
        db.flush()

        db.add(
            Disbursement(
                disbursement_id=disbursement_id,
                application_id=application_id,
                disbursement_amount=amount,
                beneficiary_reference=f"BEN-{suffix}",
                bank_reference=bank_reference,
                payment_provider="TEST_PROVIDER",
                status="PROCESSED",
                retry_attempts=0,
                initiated_at=now,
                processed_at=now,
                idempotency_key=f"WEBHOOK-IDEM-{suffix}",
            )
        )
        db.flush()

        db.add(
            InternalLedger(
                ledger_id=f"WEBHOOK-LEDGER-{suffix}",
                application_id=application_id,
                disbursement_id=disbursement_id,
                transaction_type="DISBURSEMENT",
                internal_reference=f"LEDGER-REF-{suffix}",
                transaction_amount=amount,
                transaction_date=now,
                ledger_status="POSTED",
            )
        )

        db.add(
            Reconciliation(
                reconciliation_id=f"WEBHOOK-RECON-{suffix}",
                application_id=application_id,
                disbursement_id=disbursement_id,
                transaction_type="DISBURSEMENT",
                internal_reference=f"LEDGER-REF-{suffix}",
                external_reference=bank_reference,
                transaction_amount=amount,
                transaction_date=now,
                reconciliation_status="MATCHED",
                reconciled_at=now,
            )
        )

        db.commit()
        return case

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def cleanup_processed_disbursement(case):
    db = SessionLocal()
    try:
        application_id = case["application_id"]
        disbursement_id = case["disbursement_id"]

        db.query(AuditLog).filter(
            AuditLog.application_id == application_id
        ).delete(synchronize_session=False)

        db.query(Reconciliation).filter(
            Reconciliation.disbursement_id == disbursement_id
        ).delete(synchronize_session=False)

        db.query(InternalLedger).filter(
            InternalLedger.disbursement_id == disbursement_id
        ).delete(synchronize_session=False)

        db.query(Disbursement).filter(
            Disbursement.disbursement_id == disbursement_id
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


def send_webhook(case, status, failure_reason=None):
    client = TestClient(app, raise_server_exceptions=False)

    return client.post(
        "/disbursements/webhooks/bank",
        json={
            "disbursement_id": case["disbursement_id"],
            "bank_reference": case["bank_reference"],
            "status": status,
            "bank_amount": str(case["amount"]),
            "failure_reason": failure_reason,
        },
    )


def test_repeated_success_webhook_is_audited_without_duplicate_reconciliation():
    case = seed_processed_disbursement()

    try:
        first_response = send_webhook(case, "SUCCESS")
        assert first_response.status_code == 200, first_response.text

        second_response = send_webhook(case, "SUCCESS")
        assert second_response.status_code == 200, second_response.text

        db = SessionLocal()
        try:
            disbursement = db.get(
                Disbursement,
                case["disbursement_id"],
            )
            assert disbursement.status == "PROCESSED"

            reconciliations = (
                db.query(Reconciliation)
                .filter(
                    Reconciliation.disbursement_id
                    == case["disbursement_id"],
                    Reconciliation.transaction_type == "DISBURSEMENT",
                )
                .all()
            )
            assert len(reconciliations) == 1
            assert reconciliations[0].reconciliation_status == "MATCHED"

            receipt_events = (
                db.query(AuditLog)
                .filter(
                    AuditLog.application_id == case["application_id"],
                    AuditLog.action == "BANK_WEBHOOK_RECEIVED",
                )
                .all()
            )
            assert len(receipt_events) == 2

        finally:
            db.close()

    finally:
        cleanup_processed_disbursement(case)


def test_failed_webhook_cannot_reverse_processed_disbursement():
    case = seed_processed_disbursement()

    try:
        response = send_webhook(
            case,
            "FAILED",
            failure_reason="BANK_TIMEOUT",
        )

        assert response.status_code == 409, response.text

        db = SessionLocal()
        try:
            disbursement = db.get(
                Disbursement,
                case["disbursement_id"],
            )
            assert disbursement.status == "PROCESSED"
            assert disbursement.processed_at is not None

            receipt_events = (
                db.query(AuditLog)
                .filter(
                    AuditLog.application_id == case["application_id"],
                    AuditLog.action == "BANK_WEBHOOK_RECEIVED",
                )
                .all()
            )
            assert len(receipt_events) == 1

            failure_events = (
                db.query(AuditLog)
                .filter(
                    AuditLog.application_id == case["application_id"],
                    AuditLog.action == "DISBURSEMENT_FAILED",
                )
                .all()
            )
            assert failure_events == []

        finally:
            db.close()

    finally:
        cleanup_processed_disbursement(case)