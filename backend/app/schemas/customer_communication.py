from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.underwriting import UnderwritingResult


class AdditionalInformationRequestInput(BaseModel):
    """Information supplied by an authorized officer for a draft request."""

    model_config = ConfigDict(extra="forbid")

    application_id: str = Field(min_length=1, max_length=100)
    customer_id: str = Field(min_length=1, max_length=100)

    recipient_name: str | None = Field(
        default=None,
        max_length=100,
    )

    requested_items: list[str] = Field(
        min_length=1,
        max_length=20,
    )

    contact_instructions: str | None = Field(
        default=None,
        max_length=500,
    )


class DecisionCommunicationInput(BaseModel):
    """Input for a decision-specific communication draft."""

    model_config = ConfigDict(extra="forbid")

    communication_type: Literal[
        "APPROVAL_COMMUNICATION",
        "REJECTION_COMMUNICATION",
    ]

    underwriting: UnderwritingResult

    recipient_name: str | None = Field(
        default=None,
        max_length=100,
    )

class SanctionCommunicationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_id: str = Field(min_length=1, max_length=100)
    customer_id: str = Field(min_length=1, max_length=100)
    recipient_name: str | None = Field(default=None, max_length=100)


class DisbursementCommunicationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_id: str = Field(min_length=1, max_length=100)
    customer_id: str = Field(min_length=1, max_length=100)
    recipient_name: str | None = Field(default=None, max_length=100)


class RepaymentServicingCommunicationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_id: str = Field(min_length=1, max_length=100)
    customer_id: str = Field(min_length=1, max_length=100)
    repayment_schedule_id: str = Field(min_length=1, max_length=100)
    recipient_name: str | None = Field(default=None, max_length=100)


class CustomerCommunicationDraft(BaseModel):
    """A draft that requires human review before external use."""

    model_config = ConfigDict(extra="forbid")

    communication_type: Literal[
        "ADDITIONAL_INFORMATION_REQUEST",
        "APPROVAL_COMMUNICATION",
        "REJECTION_COMMUNICATION",
        "SANCTION_COMMUNICATION",
        "DISBURSEMENT_COMMUNICATION",
        "REPAYMENT_SERVICING_COMMUNICATION",
    ]

    application_id: str
    customer_id: str

    subject: str
    body: str

    status: Literal["DRAFT_REQUIRES_HUMAN_REVIEW"] = (
        "DRAFT_REQUIRES_HUMAN_REVIEW"
    )

    human_approval_required: Literal[True] = True
    sending_enabled: Literal[False] = False

    reviewer_notes: list[str] = Field(default_factory=list)