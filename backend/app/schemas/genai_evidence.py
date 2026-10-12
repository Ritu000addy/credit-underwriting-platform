from pydantic import BaseModel, Field
from typing import Any

class GenAIEvidence(BaseModel):
    """
    Controlled evidence supplied to the GenAI underwriting layer.

    This schema contains only information required for
    summarization, explanation, and analyst assistance.
    """

    application_id: str | None = None
    customer_id: str | None = None

    # -----------------------------------------------------
    # Borrower 360 source data
    # -----------------------------------------------------

    kyc: dict[str, Any] = Field(
        default_factory=dict
    )

    credit_bureau: dict[str, Any] = Field(
        default_factory=dict
    )

    bank_cash_flow: dict[str, Any] = Field(
        default_factory=dict
    )

    employment_business: dict[str, Any] = Field(
        default_factory=dict
    )

    internal_history: dict[str, Any] = Field(
        default_factory=dict
    )

    device_behaviour: dict[str, Any] = Field(
        default_factory=dict
    )

    documents: dict[str, Any] = Field(
        default_factory=dict
    )

    # -----------------------------------------------------
    # Underwriting analysis
    # -----------------------------------------------------

    bureau_history: dict[str, Any] = Field(
        default_factory=dict
    )

    bank_income: dict[str, Any] = Field(
        default_factory=dict
    )

    fraud: dict[str, Any] = Field(
        default_factory=dict
    )
    
    policy: dict[str, Any] = Field(
        default_factory=dict
    )
    
    risk_assessment: dict[str, Any] = Field(
        default_factory=dict
    )

    decision: dict[str, Any] = Field(
        default_factory=dict
    )
    
    completeness: dict[str, Any] = Field(
        default_factory=dict
    )

    # -----------------------------------------------------
    # Deterministic findings
    # -----------------------------------------------------

    strengths: list[str] = Field(
        default_factory=list
    )

    concerns: list[str] = Field(
        default_factory=list
    )

    missing_information: list[str] = Field(
        default_factory=list
    )

    policy_exceptions: list[str] = Field(
        default_factory=list
    )