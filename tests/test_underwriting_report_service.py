from backend.app.schemas.genai_underwriting import (
    GenAIUnderwritingResult,
)
from backend.app.schemas.underwriting import UnderwritingResult
from backend.app.services.underwriting_report_service import (
    underwriting_report_service,
)


def test_generates_internal_underwriting_report():
    underwriting = UnderwritingResult(
        application_id="SYN-APP-001",
        customer_id="SYN-CUST-001",
    )

    genai = GenAIUnderwritingResult(
        status="SUCCESS",
        borrower_summary="Synthetic salaried borrower.",
        financial_summary="Monthly income is INR 80,000.",
        credit_narrative="Stable income with satisfactory repayment history.",
        strengths=["Stable income", "No reported payment defaults"],
        concerns=["Two active loans require review"],
        missing_information=["Latest salary slip"],
        policy_exceptions=[],
        officer_summary="Review existing obligations before final decision.",
        llm_analyst_narrative="Synthetic test narrative.",
        model_name="synthetic-test",
        model_version="1.0",
    )

    report = underwriting_report_service.generate(
        underwriting=underwriting,
        genai=genai,
    )

    assert report.report_type == "INTERNAL_UNDERWRITING_REPORT"
    assert report.report_version == "1.0"
    assert report.application_id == "SYN-APP-001"
    assert report.customer_id == "SYN-CUST-001"

    assert report.borrower_summary == genai.borrower_summary
    assert report.financial_analysis == genai.financial_summary
    assert report.credit_narrative == genai.credit_narrative
    assert report.officer_summary == genai.officer_summary

    assert report.strengths == genai.strengths
    assert report.concerns == genai.concerns
    assert report.risk_findings == genai.concerns
    assert report.missing_evidence == genai.missing_information
    assert report.policy_exceptions == genai.policy_exceptions

    # Optional structured underwriting sections are absent in this test.
    assert report.underwriting_decision == {}
    assert report.risk_assessment == {}
    assert report.policy_evaluation == {}
    assert report.completeness == {}

    assert report.generated_at is not None