import pytest

from backend.app.schemas.borrower360 import (
    Borrower360,
    BankCashFlowData,
    CreditBureauData,
    EmploymentBusinessData,
    InternalHistoryData,
)
from backend.app.services.bureau_history_validator import (
    BureauHistoryValidator,
)
from backend.app.services.bank_income_validator import (
    BankIncomeValidator,
)


def make_borrower(
    bureau_status=None,
    bank_status=None,
):
    return Borrower360(
        customer_id="SYNTHETIC-VERIFY-TEST",
        credit_bureau=CreditBureauData(
            score=742,
            dpd=0,
            enquiries=2,
            active_loans=1,
            total_outstanding=100000,
            write_offs=0,
            verification_status=bureau_status,
        ),
        bank_cash_flow=BankCashFlowData(
            credits=80000,
            debits=45000,
            balance=120000,
            emi=15000,
            bounce=0,
            transaction_count=120,
            income_pattern={"income_trend": "STABLE"},
            verification_status=bank_status,
        ),
        employment_business=EmploymentBusinessData(
            salary=80000,
            employer="Synthetic Employer",
        ),
        internal_history=InternalHistoryData(),
    )


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("VERIFIED", "PASS"),
        ("UNVERIFIED", "FAIL"),
        ("PENDING", "FAIL"),
        (None, "FAIL"),
    ],
)
def test_bureau_requires_verified_source(status, expected):
    result = BureauHistoryValidator().validate(
        make_borrower(bureau_status=status)
    )

    assert result.status == expected

    if expected == "FAIL":
        assert "BUREAU_DATA_NOT_VERIFIED" in result.reason_codes


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("VERIFIED", "PASS"),
        ("UNVERIFIED", "FAIL"),
        ("PENDING", "FAIL"),
        (None, "FAIL"),
    ],
)
def test_bank_analysis_requires_verified_source(status, expected):
    result = BankIncomeValidator().validate(
        make_borrower(bank_status=status)
    )

    assert result.status == expected

    if expected == "FAIL":
        assert "BANK_DATA_NOT_VERIFIED" in result.reason_codes