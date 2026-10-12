from backend.app.schemas.underwriting_report import UnderwritingReport
from backend.app.services.underwriting_report_service import (
    underwriting_report_service,
)


def test_markdown_export_preserves_underwriting_findings():
    report = UnderwritingReport(
        application_id="SYN-APP-001",
        customer_id="SYN-CUST-001",
        status="GENERATED",
        borrower_summary="Synthetic salaried borrower.",
        financial_analysis="Monthly income: INR 80,000.",
        credit_narrative="Current underwriting decision is REFER.",
        officer_summary="Human credit officer review required.",
        strengths=["Stable income"],
        risk_findings=["Risk assessment classifies this application as HIGH_RISK."],
        concerns=["Weak repayment history"],
        policy_exceptions=["Policy data requires review"],
        missing_evidence=["Latest salary slip"],
        underwriting_decision={
            "decision": "REFER",
        },
        risk_assessment={
            "risk_segment": "HIGH_RISK",
            "credit_score": 742,
            "risk_grade": "B",
            "probability_of_default": 0.023881,
            "foir": 35.63,
            "repayment_propensity": 25,
        },
        policy_evaluation={
            "policy_status": "REFER",
            "policy_version": "POL-2026.09",
        },
        completeness={
            "status": "COMPLETE",
            "missing_fields": [],
        },
    )

    markdown = underwriting_report_service.to_markdown(report)

    assert "# Internal Underwriting Report" in markdown
    assert "SYN-APP-001" in markdown
    assert "SYN-CUST-001" in markdown
    assert "Current underwriting decision is REFER." in markdown
    assert "- Decision: REFER" in markdown
    assert "- Risk segment: HIGH_RISK" in markdown
    assert "- Policy status: REFER" in markdown
    assert "Stable income" in markdown
    assert "Weak repayment history" in markdown
    assert "Latest salary slip" in markdown
    assert "The deterministic underwriting decision remains authoritative." in markdown