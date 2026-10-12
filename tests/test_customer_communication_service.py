import pytest
from pydantic import ValidationError

from backend.app.schemas.customer_communication import (
    AdditionalInformationRequestInput,
)
from backend.app.services.customer_communication_service import (
    customer_communication_service,
)


def test_additional_information_request_requires_human_review():
    request = AdditionalInformationRequestInput(
        application_id="SYN-APP-001",
        customer_id="SYN-CUST-001",
        recipient_name="Synthetic Customer",
        requested_items=[
            "Latest salary slip",
            "Recent bank statement",
            "Latest salary slip",
        ],
        contact_instructions="Contact your assigned loan officer for assistance.",
    )

    draft = (
        customer_communication_service
        .generate_additional_information_request(request)
    )

    assert draft.communication_type == "ADDITIONAL_INFORMATION_REQUEST"
    assert draft.application_id == "SYN-APP-001"
    assert draft.customer_id == "SYN-CUST-001"

    assert draft.status == "DRAFT_REQUIRES_HUMAN_REVIEW"
    assert draft.human_approval_required is True
    assert draft.sending_enabled is False

    assert "Synthetic Customer" in draft.body
    assert "Latest salary slip" in draft.body
    assert "Recent bank statement" in draft.body
    assert draft.body.count("Latest salary slip") == 1
    assert "does not represent a final credit decision" in draft.body

    assert len(draft.reviewer_notes) >= 1


def test_additional_information_request_rejects_empty_items():
    with pytest.raises(ValidationError):
        AdditionalInformationRequestInput(
            application_id="SYN-APP-001",
            customer_id="SYN-CUST-001",
            requested_items=[],
        )


def test_additional_information_request_rejects_blank_items():
    request = AdditionalInformationRequestInput(
        application_id="SYN-APP-001",
        customer_id="SYN-CUST-001",
        requested_items=["   "],
    )

    with pytest.raises(ValueError, match="REQUESTED_ITEMS_REQUIRED"):
        customer_communication_service.generate_additional_information_request(
            request
        )