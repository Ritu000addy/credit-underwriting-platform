import pytest

from backend.app.schemas.customer_communication import (
    DecisionCommunicationInput,
)
from backend.app.schemas.underwriting import (
    CreditDecisionOutput,
    UnderwritingResult,
)
from backend.app.services.customer_communication_service import (
    customer_communication_service,
)


def make_request(
    decision: str,
    communication_type: str,
    decision_application_id: str = "SYN-APP-001",
) -> DecisionCommunicationInput:
    decision_result = CreditDecisionOutput.model_construct(
        application_id=decision_application_id,
        decision=decision,
    )

    underwriting = UnderwritingResult.model_construct(
        application_id="SYN-APP-001",
        customer_id="SYN-CUST-001",
        decision=decision_result,
    )

    return DecisionCommunicationInput(
        communication_type=communication_type,
        underwriting=underwriting,
        recipient_name="Synthetic Customer",
    )


def test_approve_decision_generates_approval_draft():
    request = make_request(
        decision="APPROVE",
        communication_type="APPROVAL_COMMUNICATION",
    )

    draft = (
        customer_communication_service
        .generate_decision_communication(request)
    )

    assert draft.communication_type == "APPROVAL_COMMUNICATION"
    assert draft.status == "DRAFT_REQUIRES_HUMAN_REVIEW"
    assert draft.human_approval_required is True
    assert draft.sending_enabled is False
    assert "APPROVE" in draft.body
    assert "Synthetic Customer" in draft.body


def test_reject_decision_generates_rejection_draft():
    request = make_request(
        decision="REJECT",
        communication_type="REJECTION_COMMUNICATION",
    )

    draft = (
        customer_communication_service
        .generate_decision_communication(request)
    )

    assert draft.communication_type == "REJECTION_COMMUNICATION"
    assert draft.status == "DRAFT_REQUIRES_HUMAN_REVIEW"
    assert draft.human_approval_required is True
    assert draft.sending_enabled is False
    assert "REJECT" in draft.body


@pytest.mark.parametrize(
    ("communication_type", "expected_error"),
    [
        (
            "APPROVAL_COMMUNICATION",
            "APPROVAL_DRAFT_REQUIRES_APPROVE_DECISION",
        ),
        (
            "REJECTION_COMMUNICATION",
            "REJECTION_DRAFT_REQUIRES_REJECT_DECISION",
        ),
    ],
)
def test_refer_decision_cannot_generate_approval_or_rejection(
    communication_type: str,
    expected_error: str,
):
    request = make_request(
        decision="REFER",
        communication_type=communication_type,
    )

    with pytest.raises(ValueError, match=expected_error):
        customer_communication_service.generate_decision_communication(
            request
        )


def test_missing_decision_cannot_generate_draft():
    decision_result = CreditDecisionOutput.model_construct(
        application_id="SYN-APP-001",
        decision=None,
    )

    underwriting = UnderwritingResult.model_construct(
        application_id="SYN-APP-001",
        customer_id="SYN-CUST-001",
        decision=decision_result,
    )

    request = DecisionCommunicationInput(
        communication_type="APPROVAL_COMMUNICATION",
        underwriting=underwriting,
    )

    with pytest.raises(
        ValueError,
        match="UNDERWRITING_DECISION_REQUIRED",
    ):
        customer_communication_service.generate_decision_communication(
            request
        )


def test_mismatched_application_id_is_rejected():
    request = make_request(
        decision="APPROVE",
        communication_type="APPROVAL_COMMUNICATION",
        decision_application_id="SYN-APP-OTHER",
    )

    with pytest.raises(ValueError, match="APPLICATION_ID_MISMATCH"):
        customer_communication_service.generate_decision_communication(
            request
        )