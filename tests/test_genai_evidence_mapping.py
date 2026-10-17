from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.underwriting import UnderwritingResult
from backend.app.schemas.risk_assessment import RiskAssessmentResult

from backend.app.services.genai_underwriting_service import (
    genai_underwriting_service,
)

def test_genai_evidence_mapping_uses_minimized_synthetic_data():
    borrower = Borrower360(
        customer_id="SYN-CUST-001",
        kyc={
            "pan": "SYNTHETIC-PAN",
            "aadhaar": "SYNTHETIC-AADHAAR",
            "aadhaar_kyc_status": "VERIFIED",
            "ekyc_result": "PASS",
            "address": "Synthetic test address",
            "dob": "1990-01-01",
        },
        credit_bureau={
            "score": 742,
            "dpd": 0,
            "enquiries": 2,
            "active_loans": 2,
            "total_outstanding": 120000,
            "write_offs": 0,
        },
        bank_cash_flow={
            "credits": 80000,
            "debits": 45000,
            "balance": 120000,
            "emi": 15000,
            "bounce": 0,
            "transaction_count": 120,
            "income_pattern": {"income_trend": "STABLE"},
        },
        employment_business={
            "salary": 80000,
            "employer": "Synthetic Employer",
            "gst": None,
            "udyam": None,
            "business_vintage": None,
        },
        internal_history={
            "past_loans": [{"synthetic": True}],
            "repayment": [{"synthetic": True}],
            "dpd": [],
            "collections": [],
        },
        device_behaviour={
            "device": "ANDROID",
            "ip": "192.0.2.10",
            "velocity": "NORMAL",
            "session_patterns": {"synthetic": True},
        },
        documents={
            "payslips": [{"synthetic": True}],
            "bank_statements": [{"synthetic": True}],
            "invoices": [],
            "business_proofs": [],
        },
    )

    underwriting = UnderwritingResult(
        application_id="SYN-APP-001",
        customer_id="SYN-CUST-001",
    )

    evidence = genai_underwriting_service._build_llm_evidence(
        borrower=borrower,
        underwriting=underwriting,
        strengths=["Synthetic test strength"],
        concerns=[],
        missing_information=[],
        policy_exceptions=[],
    ).model_dump()

    # Direct identifiers and raw device data are not sent.
    assert evidence["application_id"] is None
    assert evidence["customer_id"] is None
    assert "pan" not in evidence["kyc"]
    assert "aadhaar" not in evidence["kyc"]
    assert "address" not in evidence["kyc"]
    assert "ip" not in evidence["device_behaviour"]

    # Actual schema fields are mapped correctly.
    assert evidence["credit_bureau"]["score"] == 742
    assert evidence["bank_cash_flow"]["credits"] == 80000
    assert evidence["bank_cash_flow"]["income_trend"] == "STABLE"

    # History and document content are represented as counts.
    assert evidence["internal_history"]["past_loans_count"] == 1
    assert evidence["internal_history"]["repayment_records_count"] == 1
    assert evidence["documents"]["bank_statement_count"] == 1
    assert evidence["documents"]["payslip_count"] == 1

    assert evidence["strengths"] == ["Synthetic test strength"]


def test_high_risk_narrative_rejects_lower_risk_classifications():
    underwriting = UnderwritingResult(
        application_id="SYN-APP-001",
        customer_id="SYN-CUST-001",
        risk_assessment=RiskAssessmentResult(
            status="COMPLETED",
            risk_segment="HIGH_RISK",
        ),
    )

    for narrative in (
        "The borrower is low risk.",
        "The borrower is low-risk.",
        "The borrower is medium risk.",
        "The borrower is medium-risk.",
    ):
        result = genai_underwriting_service._validate_llm_narrative(
            narrative=narrative,
            underwriting=underwriting,
        )
        assert result is None


def test_low_risk_narrative_rejects_high_risk_classification():
    underwriting = UnderwritingResult(
        application_id="SYN-APP-002",
        customer_id="SYN-CUST-002",
        risk_assessment=RiskAssessmentResult(
            status="COMPLETED",
            risk_segment="LOW_RISK",
        ),
    )

    result = genai_underwriting_service._validate_llm_narrative(
        narrative="The borrower is high risk.",
        underwriting=underwriting,
    )

    assert result is None


def test_valid_narrative_is_preserved():
    underwriting = UnderwritingResult(
        application_id="SYN-APP-003",
        customer_id="SYN-CUST-003",
        risk_assessment=RiskAssessmentResult(
            status="COMPLETED",
            risk_segment="HIGH_RISK",
        ),
    )

    narrative = (
        "The application is classified as high risk. "
        "Further review is recommended."
    )

    result = genai_underwriting_service._validate_llm_narrative(
        narrative=narrative,
        underwriting=underwriting,
    )

    assert result == narrative


def test_narrative_without_risk_assessment_is_preserved():
    underwriting = UnderwritingResult(
        application_id="SYN-APP-004",
        customer_id="SYN-CUST-004",
    )

    narrative = "Further document verification is recommended."

    result = genai_underwriting_service._validate_llm_narrative(
        narrative=narrative,
        underwriting=underwriting,
    )

    assert result == narrative