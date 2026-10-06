from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend.app.api.routes.disbursements import create_disbursement
from backend.app.api.routes.underwriting import evaluate_application
from backend.app.models.customer import Customer
from backend.app.models.disbursement import Disbursement
from backend.app.models.loan_application import LoanApplication
from backend.app.schemas.application import ApplicationCreate
from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.disbursement import DisbursementCreate


from datetime import datetime
from decimal import Decimal

from backend.app.services.collection_service import collection_service
from backend.app.services.disbursement_service import disbursement_service
from backend.app.services.repayment_schedule_service import (
    repayment_schedule_service,
)
from backend.app.services.repayment_service import repayment_service


class FakeQuery:
    def __init__(self, result):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result


class FakeUnderwritingDB:
    def __init__(
        self,
        application_record,
        customer,
    ):
        self.application_record = application_record
        self.customer = customer

    def get(self, model, key):
        if model is LoanApplication:
            return self.application_record

        if model is Customer:
            return self.customer

        return None


class FakeDisbursementDB:
    def __init__(self, existing_disbursement):
        self.existing_disbursement = existing_disbursement

    def query(self, model):
        assert model is Disbursement
        return FakeQuery(self.existing_disbursement)


def build_borrower(customer_id):
    return Borrower360(
        customer_id=customer_id,
        kyc={
            "pan": "ABCDE1234F",
            "aadhaar": "123456789012",
            "aadhaar_kyc_status": "VERIFIED",
            "ekyc_result": "VERIFIED",
            "dob": "1993-03-01",
            "address": "Pune, Maharashtra",
        },
        credit_bureau={
            "score": 750,
            "dpd": 0,
            "enquiries": 2,
            "active_loans": 1,
            "total_outstanding": 100000,
            "write_offs": 0,
        },
        bank_cash_flow={
            "credits": 100000,
            "debits": 40000,
            "balance": 60000,
            "emi": 15000,
            "bounce": 0,
            "transaction_count": 30,
        },
        employment_business={
            "salary": 75000,
            "employer": "TEST EMPLOYER",
            "business_vintage": 24,
        },
        internal_history={
            "past_loans": [{"loan_id": "L1"}],
            "repayment": [{"status": "PAID"}],
            "dpd": [],
            "collections": [],
        },
        device_behaviour={
            "device": "TEST-DEVICE",
            "ip": "127.0.0.1",
            "velocity": {
                "applications_last_24h": 1
            },
            "session_patterns": {
                "multiple_devices": False
            },
        },
        documents={
            "payslips": [{"verified": True}],
            "bank_statements": [{"verified": True}],
        },
    )


def test_application_customer_mismatch_returns_400():
    application = ApplicationCreate(
        application_id="NEG-APP-001",
        customer_id="CUST-REQUEST",
        requested_amount=150000,
        loan_tenure_months=12,
    )

    borrower = build_borrower("CUST-REQUEST")

    db = FakeUnderwritingDB(
        application_record=SimpleNamespace(
            customer_id="CUST-PERSISTED"
        ),
        customer=SimpleNamespace(
            customer_id="CUST-REQUEST"
        ),
    )

    with pytest.raises(HTTPException) as exc:
        evaluate_application(
            application=application,
            borrower=borrower,
            db=db,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "APPLICATION_CUSTOMER_MISMATCH"


def test_borrower_customer_mismatch_returns_400():
    application = ApplicationCreate(
        application_id="NEG-APP-002",
        customer_id="CUST-001",
        requested_amount=150000,
        loan_tenure_months=12,
    )

    borrower = build_borrower("CUST-WRONG")

    db = FakeUnderwritingDB(
        application_record=SimpleNamespace(
            customer_id="CUST-001"
        ),
        customer=SimpleNamespace(
            customer_id="CUST-001"
        ),
    )

    with pytest.raises(HTTPException) as exc:
        evaluate_application(
            application=application,
            borrower=borrower,
            db=db,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "BORROWER_CUSTOMER_MISMATCH"


def build_disbursement_request(amount=50000):
    return DisbursementCreate(
        application_id="APP-001",
        disbursement_amount=amount,
        sanction_id="SAN-001",
        beneficiary_reference="BEN-001",
        payment_provider="TEST-BANK",
        idempotency_key="NEG-IDEMP-001",
    )


def build_existing_disbursement(amount=50000):
    return SimpleNamespace(
        application_id="APP-001",
        sanction_id="SAN-001",
        disbursement_amount=amount,
        beneficiary_reference="BEN-001",
        payment_provider="TEST-BANK",
    )


def test_idempotency_key_payload_mismatch_returns_409():
    request = build_disbursement_request(
        amount=60000
    )

    existing = build_existing_disbursement(
        amount=50000
    )

    db = FakeDisbursementDB(
        existing_disbursement=existing
    )

    with pytest.raises(HTTPException) as exc:
        create_disbursement(
            disbursement=request,
            db=db,
        )

    assert exc.value.status_code == 409
    assert (
        exc.value.detail
        == "IDEMPOTENCY_KEY_PAYLOAD_MISMATCH"
    )


def test_idempotency_same_payload_returns_existing_record():
    request = build_disbursement_request(
        amount=50000
    )

    existing = build_existing_disbursement(
        amount=50000
    )

    db = FakeDisbursementDB(
        existing_disbursement=existing
    )

    result = create_disbursement(
        disbursement=request,
        db=db,
    )

    assert result is existing

def test_underwriting_missing_application_returns_404():
    application = ApplicationCreate(
        application_id="NEG-APP-MISSING",
        customer_id="CUST-001",
        requested_amount=150000,
        loan_tenure_months=12,
    )

    borrower = build_borrower("CUST-001")

    db = FakeUnderwritingDB(
        application_record=None,
        customer=None,
    )

    with pytest.raises(HTTPException) as exc:
        evaluate_application(
            application=application,
            borrower=borrower,
            db=db,
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "APPLICATION_NOT_FOUND"


def test_underwriting_missing_customer_returns_404():
    application = ApplicationCreate(
        application_id="NEG-APP-NO-CUSTOMER",
        customer_id="CUST-MISSING",
        requested_amount=150000,
        loan_tenure_months=12,
    )

    borrower = build_borrower("CUST-MISSING")

    db = FakeUnderwritingDB(
        application_record=SimpleNamespace(
            customer_id="CUST-MISSING"
        ),
        customer=None,
    )

    with pytest.raises(HTTPException) as exc:
        evaluate_application(
            application=application,
            borrower=borrower,
            db=db,
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "CUSTOMER_NOT_FOUND"


def test_disbursement_invalid_initial_status_is_rejected():
    with pytest.raises(
        ValueError,
        match="INVALID_INITIAL_DISBURSEMENT_STATUS",
    ):
        disbursement_service.create_disbursement(
            db=None,
            disbursement_id="NEG-DISB-001",
            application_id="APP-001",
            disbursement_amount=Decimal("50000.00"),
            status="INITIATED",
        )


def test_repayment_invalid_initial_status_is_rejected():
    with pytest.raises(
        ValueError,
        match="INVALID_INITIAL_REPAYMENT_STATUS",
    ):
        repayment_service.create_repayment(
            db=None,
            repayment_id="NEG-REPAY-001",
            application_id="APP-001",
            repayment_amount=Decimal("10000.00"),
            status="PENDING",
        )


def test_repayment_schedule_invalid_initial_status_is_rejected():
    with pytest.raises(
        ValueError,
        match="INVALID_INITIAL_REPAYMENT_SCHEDULE_STATUS",
    ):
        repayment_schedule_service.create_installment(
            db=None,
            repayment_schedule_id="NEG-RS-001",
            application_id="APP-001",
            disbursement_id="DISB-001",
            installment_number=1,
            due_date=datetime.utcnow(),
            principal_due=Decimal("9000.00"),
            interest_due=Decimal("1000.00"),
            total_due=Decimal("10000.00"),
            outstanding_principal=Decimal("9000.00"),
            status="PAID",
        )


def test_collection_invalid_initial_status_is_rejected():
    with pytest.raises(
        ValueError,
        match="INVALID_INITIAL_COLLECTION_STATUS",
    ):
        collection_service.create_collection(
            db=None,
            collection_id="NEG-COL-001",
            application_id="APP-001",
            collection_type="EMI",
            due_amount=Decimal("10000.00"),
            collected_amount=Decimal("0.00"),
            outstanding_amount=Decimal("10000.00"),
            days_past_due=0,
            status="INVALID",
        )