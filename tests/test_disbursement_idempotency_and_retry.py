
import uuid
import pytest
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.app.database import SessionLocal
from backend.app.main import app
from backend.app.models.audit_log import AuditLog
from backend.app.models.customer import Customer
from backend.app.models.disbursement import Disbursement
from backend.app.models.internal_ledger import InternalLedger
from backend.app.models.loan_application import LoanApplication
from backend.app.models.reconciliation import Reconciliation
from backend.app.services.bank_routing_service import bank_routing_service

pytestmark = pytest.mark.usefixtures("operations_auth")

def seed_case(
    *,
    status="CREATED",
    amount=Decimal("1250.00"),
    retry_attempts=0,
    failure_reason=None,
    seed_ledger=False,
):
    suffix = uuid.uuid4().hex[:12].upper()
    application_id = f"IDEM-APP-{suffix}"
    customer_id = f"IDEM-CUST-{suffix}"
    disbursement_id = f"IDEM-DISB-{suffix}"
    idempotency_key = f"IDEM-KEY-{suffix}"
    now = datetime.utcnow()

    case = {
        "application_id": application_id,
        "customer_id": customer_id,
        "disbursement_id": disbursement_id,
        "idempotency_key": idempotency_key,
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
                product="SYNTHETIC_TEST",
                requested_amount=amount,
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
                payment_provider="TEST_PROVIDER",
                status=status,
                idempotency_key=idempotency_key,
                retry_attempts=retry_attempts,
                failure_reason=failure_reason,
                initiated_at=now,
            )
        )
        db.flush()

        if seed_ledger:
            db.add(
                InternalLedger(
                    ledger_id=f"IDEM-LEDGER-{suffix}",
                    application_id=application_id,
                    disbursement_id=disbursement_id,
                    transaction_type="DISBURSEMENT",
                    internal_reference=f"LEDGER-REF-{suffix}",
                    transaction_amount=amount,
                    transaction_date=now,
                    ledger_status="POSTED",
                )
            )

        db.commit()
        return case

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def cleanup_case(case):
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


def create_request(case, amount=None):
    return {
        "application_id": case["application_id"],
        "disbursement_amount": str(
            amount if amount is not None else case["amount"]
        ),
        "sanction_id": None,
        "beneficiary_reference": (
            f"BEN-{case['disbursement_id'].removeprefix('IDEM-DISB-')}"
        ),
        "payment_provider": "TEST_PROVIDER",
        "idempotency_key": case["idempotency_key"],
    }


def test_identical_create_request_returns_existing_disbursement():
    case = seed_case()

    try:
        client = TestClient(app, raise_server_exceptions=False)

        response = client.post(
            "/disbursements",
            json=create_request(case),
        )

        assert response.status_code == 200, response.text
        assert case["disbursement_id"] in response.text

        db = SessionLocal()
        try:
            matching = (
                db.query(Disbursement)
                .filter(
                    Disbursement.idempotency_key
                    == case["idempotency_key"]
                )
                .all()
            )

            assert len(matching) == 1
            assert matching[0].disbursement_id == case["disbursement_id"]
            assert matching[0].status == "CREATED"

        finally:
            db.close()

    finally:
        cleanup_case(case)


def test_reusing_idempotency_key_with_different_amount_returns_conflict():
    case = seed_case()

    try:
        client = TestClient(app, raise_server_exceptions=False)

        response = client.post(
            "/disbursements",
            json=create_request(
                case,
                amount=case["amount"] + Decimal("100.00"),
            ),
        )

        assert response.status_code == 409, response.text
        assert "IDEMPOTENCY_KEY_PAYLOAD_MISMATCH" in response.text

        db = SessionLocal()
        try:
            matching = (
                db.query(Disbursement)
                .filter(
                    Disbursement.idempotency_key
                    == case["idempotency_key"]
                )
                .all()
            )

            assert len(matching) == 1
            assert matching[0].disbursement_amount == case["amount"]

        finally:
            db.close()

    finally:
        cleanup_case(case)


def test_retry_does_not_duplicate_existing_ledger_or_route_twice(monkeypatch):
    case = seed_case(
        status="FAILED",
        retry_attempts=1,
        failure_reason="BANK_TIMEOUT",
        seed_ledger=True,
        amount=Decimal("1000.00"),
    )

    routing_calls = []

    def successful_routing(**kwargs):
        routing_calls.append(kwargs)
        return SimpleNamespace(
            success=True,
            provider="TEST_PROVIDER",
            routing_reference=f"ROUTE-{case['disbursement_id']}",
            failure_reason=None,
        )

    monkeypatch.setattr(
        bank_routing_service,
        "route_disbursement",
        successful_routing,
    )

    try:
        client = TestClient(app, raise_server_exceptions=False)
        endpoint = f"/disbursements/{case['disbursement_id']}/retry"

        first_response = client.post(endpoint)
        assert first_response.status_code == 200, first_response.text

        second_response = client.post(endpoint)
        assert second_response.status_code == 200, second_response.text

        db = SessionLocal()
        try:
            disbursement = db.get(
                Disbursement,
                case["disbursement_id"],
            )

            assert disbursement.status == "INITIATED"
            assert disbursement.retry_attempts == 2
            assert disbursement.failure_reason is None

            ledger_entries = (
                db.query(InternalLedger)
                .filter(
                    InternalLedger.disbursement_id
                    == case["disbursement_id"],
                    InternalLedger.transaction_type == "DISBURSEMENT",
                )
                .all()
            )

            assert len(ledger_entries) == 1

            # Only the first retry should reach the provider.
            assert len(routing_calls) == 1

        finally:
            db.close()

    finally:
        cleanup_case(case)


def test_retry_limit_prevents_another_provider_attempt(monkeypatch):
    case = seed_case(
        status="FAILED",
        retry_attempts=3,
        failure_reason="BANK_TIMEOUT",
    )

    routing_calls = []

    def unexpected_routing(**kwargs):
        routing_calls.append(kwargs)
        raise AssertionError(
            "Provider routing must not run after the retry limit"
        )

    monkeypatch.setattr(
        bank_routing_service,
        "route_disbursement",
        unexpected_routing,
    )

    try:
        client = TestClient(app, raise_server_exceptions=False)

        response = client.post(
            f"/disbursements/{case['disbursement_id']}/retry"
        )

        assert response.status_code == 200, response.text
        assert "MAX_RETRY_ATTEMPTS_EXCEEDED" in response.text
        assert routing_calls == []

        db = SessionLocal()
        try:
            disbursement = db.get(
                Disbursement,
                case["disbursement_id"],
            )

            assert disbursement.status == "FAILED"
            assert disbursement.retry_attempts == 3

        finally:
            db.close()

    finally:
        cleanup_case(case)
