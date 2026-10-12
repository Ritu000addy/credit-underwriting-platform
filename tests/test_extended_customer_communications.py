from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from backend.app.schemas.customer_communication import (
    DisbursementCommunicationInput,
    RepaymentServicingCommunicationInput,
    SanctionCommunicationInput,
)
from backend.app.services.customer_communication_service import (
    customer_communication_service as service,
)


def test_sanction_draft_uses_persisted_terms():
    payload = SanctionCommunicationInput(
        application_id="APP-COMM-001",
        customer_id="CUST-COMM-001",
        recipient_name="Synthetic Customer",
    )
    sanction = SimpleNamespace(
        application_id="APP-COMM-001",
        sanction_status="APPROVED",
        sanctioned_amount=Decimal("150000.00"),
        sanctioned_tenure=12,
        sanctioned_emi=Decimal("13327.32"),
        interest_rate=Decimal("12.0000"),
        expires_at=datetime(2026, 12, 31),
        terms_and_conditions="Synthetic approved terms",
    )

    draft = service.generate_sanction_communication(payload, sanction)

    assert draft.communication_type == "SANCTION_COMMUNICATION"
    assert "150,000.00" in draft.body
    assert "13,327.32" in draft.body
    assert draft.human_approval_required is True
    assert draft.sending_enabled is False


def test_sanction_draft_rejects_unapproved_sanction():
    payload = SanctionCommunicationInput(
        application_id="APP-COMM-002",
        customer_id="CUST-COMM-002",
    )
    sanction = SimpleNamespace(
        application_id="APP-COMM-002",
        sanction_status="PENDING",
    )

    with pytest.raises(ValueError, match="SANCTION_NOT_APPROVED"):
        service.generate_sanction_communication(payload, sanction)


def test_disbursement_draft_requires_processed_status():
    payload = DisbursementCommunicationInput(
        application_id="APP-COMM-003",
        customer_id="CUST-COMM-003",
    )
    disbursement = SimpleNamespace(
        application_id="APP-COMM-003",
        status="PROCESSING",
        disbursement_amount=Decimal("150000.00"),
    )

    with pytest.raises(ValueError, match="DISBURSEMENT_NOT_CONFIRMED"):
        service.generate_disbursement_communication(
            payload,
            disbursement,
        )


def test_processed_disbursement_generates_reviewable_draft():
    payload = DisbursementCommunicationInput(
        application_id="APP-COMM-004",
        customer_id="CUST-COMM-004",
    )
    disbursement = SimpleNamespace(
        application_id="APP-COMM-004",
        status="PROCESSED",
        disbursement_amount=Decimal("150000.00"),
        processed_at=datetime(2026, 10, 10),
    )

    draft = service.generate_disbursement_communication(
        payload,
        disbursement,
    )

    assert draft.communication_type == "DISBURSEMENT_COMMUNICATION"
    assert "150,000.00" in draft.body
    assert draft.sending_enabled is False


def test_pending_installment_generates_servicing_draft():
    payload = RepaymentServicingCommunicationInput(
        application_id="APP-COMM-005",
        customer_id="CUST-COMM-005",
        repayment_schedule_id="SCHEDULE-COMM-005",
    )
    schedule = SimpleNamespace(
        application_id="APP-COMM-005",
        repayment_schedule_id="SCHEDULE-COMM-005",
        status="PENDING",
        installment_number=1,
        due_date=datetime(2026, 11, 1),
        total_due=Decimal("13327.32"),
    )

    draft = service.generate_repayment_servicing_communication(
        payload,
        schedule,
    )

    assert draft.communication_type == "REPAYMENT_SERVICING_COMMUNICATION"
    assert "pending" in draft.body.lower()
    assert "13,327.32" in draft.body
    assert draft.human_approval_required is True
    assert draft.sending_enabled is False


def test_paid_installment_requires_successful_repayment_evidence():
    payload = RepaymentServicingCommunicationInput(
        application_id="APP-COMM-006",
        customer_id="CUST-COMM-006",
        repayment_schedule_id="SCHEDULE-COMM-006",
    )
    schedule = SimpleNamespace(
        application_id="APP-COMM-006",
        repayment_schedule_id="SCHEDULE-COMM-006",
        status="PAID",
        installment_number=1,
        due_date=datetime(2026, 10, 1),
        total_due=Decimal("13327.32"),
    )

    with pytest.raises(
        ValueError,
        match="REPAYMENT_CONFIRMATION_EVIDENCE_MISSING",
    ):
        service.generate_repayment_servicing_communication(
            payload,
            schedule,
            repayment=None,
        )