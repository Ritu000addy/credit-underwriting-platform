from pydantic import BaseModel, Field


class GenAILLMResponse(BaseModel):
    borrower_summary: str | None = None
    financial_summary: str | None = None
    credit_narrative: str | None = None

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

    officer_summary: str | None = None
    llm_analyst_narrative: str | None = None