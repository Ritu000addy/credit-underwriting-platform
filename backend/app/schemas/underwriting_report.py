from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

class UnderwritingReport(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
    )

    report_type: str = "INTERNAL_UNDERWRITING_REPORT"
    report_version: str = "1.0"
    generated_at: datetime = Field(
        default_factory = lambda: datetime.now(timezone.utc)
    )

    application_id: str 
    customer_id: str 
    status: str

    borrower_summary: str | None = None
    financial_analysis: str | None = None
    credit_narrative: str | None = None
    officer_summary: str | None = None
    
    strengths: list[str] = Field(default_factory=list)
    risk_findings: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    policy_exceptions: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    
    underwriting_decision: dict[str, Any] = Field(default_factory=dict)
    risk_assessment: dict[str, Any] = Field(default_factory=dict)
    policy_evaluation: dict[str, Any] = Field(default_factory=dict)
    completeness: dict[str, Any] = Field(default_factory=dict)