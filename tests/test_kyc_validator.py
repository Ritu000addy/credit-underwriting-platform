import pytest

from backend.app.schemas.borrower360 import Borrower360, KYCData
from backend.app.services.kyc_validator import KYCValidator


@pytest.fixture
def validator():
    return KYCValidator()


def make_borrower(
    *,
    pan="ABCDE1234F",
    ekyc_result="VERIFIED",
    aadhaar_kyc_status=None,
    dob="1993-03-01",
):
    return Borrower360(
        customer_id="CUST-KYC-TEST",
        kyc=KYCData(
            pan=pan,
            ekyc_result=ekyc_result,
            aadhaar_kyc_status=aadhaar_kyc_status,
            dob=dob,
        ),
    )


DEFAULT_POLICY = {
    "pan_required": True,
    "ekyc_required": True,
    "required_ekyc_result": "VERIFIED",
    "aadhaar_kyc_required": False,
}


def test_verified_ekyc_passes_when_aadhaar_is_optional(validator):
    result = validator.validate(
        make_borrower(),
        kyc_config=DEFAULT_POLICY,
    )

    assert result.status == "PASS"
    assert result.reason_codes == []
    aadhaar_check = next(
        check for check in result.checks
        if check.check_id == "AADHAAR_KYC"
    )
    assert aadhaar_check.status == "NOT_REQUIRED"


@pytest.mark.parametrize(
    ("ekyc_result", "expected_reason"),
    [
        ("PENDING", "KYC_EKYC_PENDING"),
        ("FAILED", "KYC_EKYC_NOT_VERIFIED"),
        (None, "KYC_EKYC_MISSING"),
    ],
)
def test_unverified_or_missing_ekyc_fails(
    validator,
    ekyc_result,
    expected_reason,
):
    result = validator.validate(
        make_borrower(ekyc_result=ekyc_result),
        kyc_config=DEFAULT_POLICY,
    )

    assert result.status == "FAIL"
    assert expected_reason in result.reason_codes


def test_required_aadhaar_pending_fails(validator):
    policy = {
        **DEFAULT_POLICY,
        "aadhaar_kyc_required": True,
    }

    result = validator.validate(
        make_borrower(aadhaar_kyc_status="PENDING"),
        kyc_config=policy,
    )

    assert result.status == "FAIL"
    assert "KYC_AADHAAR_PENDING" in result.reason_codes


def test_required_aadhaar_verified_passes(validator):
    policy = {
        **DEFAULT_POLICY,
        "aadhaar_kyc_required": True,
    }

    result = validator.validate(
        make_borrower(aadhaar_kyc_status="VERIFIED"),
        kyc_config=policy,
    )

    assert result.status == "PASS"


def test_missing_required_pan_fails(validator):
    result = validator.validate(
        make_borrower(pan=None),
        kyc_config=DEFAULT_POLICY,
    )

    assert result.status == "FAIL"
    assert "KYC_PAN_MISSING" in result.reason_codes


def test_missing_dob_fails(validator):
    result = validator.validate(
        make_borrower(dob=None),
        kyc_config=DEFAULT_POLICY,
    )

    assert result.status == "FAIL"
    assert "KYC_DOB_MISSING" in result.reason_codes