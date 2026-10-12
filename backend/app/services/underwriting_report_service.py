from typing import Any

from pydantic import BaseModel

from backend.app.schemas.genai_underwriting import GenAIUnderwritingResult
from backend.app.schemas.underwriting import UnderwritingResult
from backend.app.schemas.underwriting_report import UnderwritingReport


def _dump_section(value: BaseModel | None) -> dict[str, Any]:
    """Convert an optional Pydantic model into a JSON-compatible dictionary."""
    if value is None:
        return {}

    return value.model_dump(mode="json", exclude_none=True)


class UnderwritingReportService:
    """Build a structured internal report from existing underwriting outputs."""

    def generate(
        self,
        underwriting: UnderwritingResult,
        genai: GenAIUnderwritingResult,
    ) -> UnderwritingReport:
        if not underwriting.application_id.strip():
            raise ValueError("APPLICATION_ID_REQUIRED")

        if not underwriting.customer_id.strip():
            raise ValueError("CUSTOMER_ID_REQUIRED")

        concerns = list(genai.concerns or [])

        return UnderwritingReport(
            report_type="INTERNAL_UNDERWRITING_REPORT",
            report_version="1.0",
            application_id=underwriting.application_id,
            customer_id=underwriting.customer_id,
            status="GENERATED",

            borrower_summary=genai.borrower_summary,
            financial_analysis=genai.financial_summary,
            credit_narrative=(
                genai.credit_narrative
                or genai.llm_analyst_narrative
            ),
            officer_summary=genai.officer_summary,

            strengths=list(genai.strengths or []),
            risk_findings=concerns.copy(),
            concerns=concerns,
            policy_exceptions=list(genai.policy_exceptions or []),
            missing_evidence=list(genai.missing_information or []),

            underwriting_decision=_dump_section(underwriting.decision),
            risk_assessment=_dump_section(underwriting.risk_assessment),
            policy_evaluation=_dump_section(underwriting.policy),
            completeness=_dump_section(underwriting.completeness),
        )

    def to_markdown(self, report: UnderwritingReport) -> str:
        decision = report.underwriting_decision or {}
        risk = report.risk_assessment or {}
        policy = report.policy_evaluation or {}
        completeness = report.completeness or {}

        findings = list(
            dict.fromkeys(
                (report.risk_findings or [])
                + (report.concerns or [])
            )
        )

        def bullet_list(items: list[str]) -> str:
            if not items:
                return "- None recorded"
            return "\n".join(f"- {item}" for item in items)

        def value_or_unknown(value: Any) -> str:
            if value is None or value == "":
                return "Not recorded"
            return str(value)

        lines = [
            "# Internal Underwriting Report",
            "",
            f"**Report version:** {report.report_version}",
            f"**Generated at (UTC):** {report.generated_at.isoformat()}",
            f"**Application ID:** {report.application_id}",
            f"**Customer ID:** {report.customer_id}",
            f"**Report status:** {report.status}",
            "",
            "## Borrower Summary",
            report.borrower_summary or "Not available.",
            "",
            "## Financial Analysis",
            report.financial_analysis or "Not available.",
            "",
            "## Credit Narrative",
            report.credit_narrative or "Not available.",
            "",
            "## Underwriting Outcome",
            f"- Decision: {value_or_unknown(decision.get('decision'))}",
            f"- Policy status: {value_or_unknown(policy.get('policy_status'))}",
            f"- Policy version: {value_or_unknown(policy.get('policy_version'))}",
            "",
            "## Risk Assessment",
            f"- Risk segment: {value_or_unknown(risk.get('risk_segment'))}",
            f"- Credit score: {value_or_unknown(risk.get('credit_score'))}",
            f"- Risk grade: {value_or_unknown(risk.get('risk_grade'))}",
            f"- Probability of default: {value_or_unknown(risk.get('probability_of_default'))}",
            f"- FOIR: {value_or_unknown(risk.get('foir'))}",
            f"- Repayment propensity: {value_or_unknown(risk.get('repayment_propensity'))}",
            "",
            "## Strengths",
            bullet_list(report.strengths),
            "",
            "## Risk Findings and Concerns",
            bullet_list(findings),
            "",
            "## Policy Exceptions",
            bullet_list(report.policy_exceptions),
            "",
            "## Missing Evidence",
            bullet_list(report.missing_evidence),
            "",
            "## Data Completeness",
            f"- Status: {value_or_unknown(completeness.get('status'))}",
            "- Missing fields:",
            bullet_list(completeness.get("missing_fields", [])),
            "",
            "## Credit Officer Summary",
            report.officer_summary or "Not available.",
            "",
            "---",
            "*Internal underwriting report for human credit review. "
            "The deterministic underwriting decision remains authoritative.*",
            "",
        ]

        return "\n".join(lines)

underwriting_report_service = UnderwritingReportService()