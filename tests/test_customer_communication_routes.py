from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.app.api.routes import customer_communications as routes
from backend.app.schemas.customer_communication import (
    DisbursementCommunicationInput,
    RepaymentServicingCommunicationInput,
    SanctionCommunicationInput,
)


def make_request():
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/customer-communications/test",
        "raw_path": b"/customer-communications/test",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 123),
        "server": ("testserver", 80),
    }
    request = Request(scope)
    request.state.request_id = "REQ-COMM-ROUTE-TEST"
    return request


class FakeQuery:
    def __init__(self, result):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self.result


class FakeDB:
    def __init__(
        self,
        application,
        sanction=None,
        disbursement=None,
        schedule=None,
        repayment=None,
    ):
        self.application = application
        self.sanction = sanction
        self.disbursement = disbursement
        self.schedule = schedule
        self.repayment = repayment

    def get(self, model, identifier):
        if model is routes.LoanApplication:
            if self.application.application_id == identifier:
                return self.application
            return None

        if model is routes.RepaymentSchedule:
            if (
                self.schedule is not None
                and self.schedule.repayment_schedule_id == identifier
            ):
                return self.schedule
            return None

        return None

    def query(self, model):
        if model is routes.Sanction:
            return FakeQuery(self.sanction)

        if model is routes.Disbursement:
            return FakeQuery(self.disbursement)

        if model is routes.Repayment:
            return FakeQuery(self.repayment)

        raise AssertionError(f"Unexpected query model: {model}")


def setup_route_test(monkeypatch):
    events = []

    monkeypatch.setattr(
        routes,
        "log_workflow_event",
        lambda **kwargs: events.append(kwargs),
    )
    monkeypatch.setattr(
        routes,
        "success_response",
        lambda **kwargs: kwargs,
    )

    application = SimpleNamespace(
        application_id="APP-COMM-ROUTE-001",
        customer_id="CUST-COMM-ROUTE-001",
    )

    return events, application


def assert_draft_response(response, events, workflow):
    draft = response["data"]

    assert draft.status == "DRAFT_REQUIRES_HUMAN_REVIEW"
    assert draft.human_approval_required is True
    assert draft.sending_enabled is False

    assert [event["event"] for event in events] == [
        "started",
        "completed",
    ]
    assert all(event["workflow"] == workflow for event in events)
    assert events[-1]["status"] == "DRAFT_REQUIRES_HUMAN_REVIEW"


def test_sanction_draft_route(monkeypatch):
    events, application = setup_route_test(monkeypatch)

    sanction = SimpleNamespace(
        application_id=application.application_id,
        sanction_status="APPROVED",
        sanctioned_amount=Decimal("150000.00"),
        sanctioned_tenure=12,
        sanctioned_emi=Decimal("13327.32"),
        interest_rate=Decimal("12.0000"),
        expires_at=datetime(2026, 12, 31),
        terms_and_conditions="Synthetic approved terms",
    )
    db = FakeDB(application, sanction=sanction)

    response = routes.create_sanction_communication_draft(
        payload=SanctionCommunicationInput(
            application_id=application.application_id,
            customer_id=application.customer_id,
            recipient_name="Synthetic Customer",
        ),
        request=make_request(),
        db=db,
    )

    assert_draft_response(
        response, events, "sanction_communication_draft"
    )
    assert response["data"].communication_type == "SANCTION_COMMUNICATION"
    assert "150,000.00" in response["data"].body


def test_disbursement_draft_route(monkeypatch):
    events, application = setup_route_test(monkeypatch)

    disbursement = SimpleNamespace(
        application_id=application.application_id,
        status="PROCESSED",
        disbursement_amount=Decimal("150000.00"),
        processed_at=datetime(2026, 10, 10),
    )
    db = FakeDB(application, disbursement=disbursement)

    response = routes.create_disbursement_communication_draft(
        payload=DisbursementCommunicationInput(
            application_id=application.application_id,
            customer_id=application.customer_id,
        ),
        request=make_request(),
        db=db,
    )

    assert_draft_response(
        response, events, "disbursement_communication_draft"
    )
    assert (
        response["data"].communication_type
        == "DISBURSEMENT_COMMUNICATION"
    )
    assert "150,000.00" in response["data"].body


def test_repayment_servicing_draft_route(monkeypatch):
    events, application = setup_route_test(monkeypatch)

    schedule = SimpleNamespace(
        application_id=application.application_id,
        repayment_schedule_id="SCHEDULE-COMM-ROUTE-001",
        status="PENDING",
        installment_number=1,
        due_date=datetime(2026, 11, 1),
        total_due=Decimal("13327.32"),
    )
    db = FakeDB(application, schedule=schedule)

    response = routes.create_repayment_servicing_communication_draft(
        payload=RepaymentServicingCommunicationInput(
            application_id=application.application_id,
            customer_id=application.customer_id,
            repayment_schedule_id=schedule.repayment_schedule_id,
        ),
        request=make_request(),
        db=db,
    )

    assert_draft_response(
        response, events, "repayment_servicing_communication_draft"
    )
    assert (
        response["data"].communication_type
        == "REPAYMENT_SERVICING_COMMUNICATION"
    )
    assert "pending" in response["data"].body.lower()


def test_draft_route_rejects_customer_application_mismatch(monkeypatch):
    events, application = setup_route_test(monkeypatch)
    db = FakeDB(application)

    with pytest.raises(HTTPException) as exc_info:
        routes.create_sanction_communication_draft(
            payload=SanctionCommunicationInput(
                application_id=application.application_id,
                customer_id="CUST-WRONG",
            ),
            request=make_request(),
            db=db,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "APPLICATION_CUSTOMER_MISMATCH"
    assert [event["event"] for event in events] == [
        "started",
        "failed",
    ]
    assert (
        events[-1]["error_code"]
        == "COMMUNICATION_SOURCE_VALIDATION_FAILED"
    )


def test_disbursement_draft_rejects_unconfirmed_status(monkeypatch):
    events, application = setup_route_test(monkeypatch)

    disbursement = SimpleNamespace(
        application_id=application.application_id,
        status="PROCESSING",
        disbursement_amount=Decimal("150000.00"),
        processed_at=None,
    )
    db = FakeDB(application, disbursement=disbursement)

    with pytest.raises(HTTPException) as exc_info:
        routes.create_disbursement_communication_draft(
            payload=DisbursementCommunicationInput(
                application_id=application.application_id,
                customer_id=application.customer_id,
            ),
            request=make_request(),
            db=db,
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "DISBURSEMENT_NOT_CONFIRMED"
    assert [event["event"] for event in events] == [
        "started",
        "failed",
    ]