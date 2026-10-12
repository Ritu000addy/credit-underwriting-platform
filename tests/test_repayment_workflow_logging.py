from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.app.api.routes import repayments as routes


def make_request():
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/repayments/record",
        "raw_path": b"/repayments/record",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 123),
        "server": ("testserver", 80),
    }

    request = Request(scope)
    request.state.request_id = "REQ-REPAYMENT-LOG-TEST"
    return request


def make_request_body():
    return SimpleNamespace(
        application_id="APP-REP-LOG-001",
        repayment_schedule_id="SCHEDULE-REP-001",
        repayment_amount=Decimal("1000.00"),
        repayment_reference="SYNTHETIC-REF-001",
        payment_mode="UPI",
        payment_provider="TEST-PROVIDER",
    )


def setup_test(monkeypatch):
    events = []
    rollbacks = []

    db = SimpleNamespace(
        rollback=lambda: rollbacks.append("rollback")
    )

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

    monkeypatch.setattr(
        routes,
        "RepaymentResponse",
        SimpleNamespace(model_validate=lambda value: value),
    )

    return events, rollbacks, db


def assert_event_sequence(events, expected):
    assert [event["event"] for event in events] == expected
    assert all(
        event["workflow"] == "repayment_recording"
        for event in events
    )


def test_record_repayment_logs_success(monkeypatch):
    events, rollbacks, db = setup_test(monkeypatch)
    request_body = make_request_body()

    repayment = SimpleNamespace(
        repayment_id="REP-LOG-001",
        application_id=request_body.application_id,
        repayment_schedule_id=request_body.repayment_schedule_id,
        status="SUCCESS",
    )

    def fake_record_repayment(**kwargs):
        assert kwargs["db"] is db
        assert kwargs["application_id"] == request_body.application_id
        return repayment

    monkeypatch.setattr(
        routes.repayment_service,
        "record_repayment",
        fake_record_repayment,
    )

    response = routes.record_repayment(
        request=request_body,
        api_request=make_request(),
        db=db,
    )

    assert_event_sequence(events, ["started", "completed"])
    assert events[0]["application_id"] == request_body.application_id
    assert events[-1]["entity_id"] == "REP-LOG-001"
    assert response["data"] is repayment
    assert rollbacks == []

    # Financial request fields must not be included in event metadata.
    for event in events:
        assert "repayment_amount" not in event
        assert "repayment_reference" not in event
        assert "payment_provider" not in event


def test_record_repayment_value_error_logs_failure_and_rolls_back(
    monkeypatch,
):
    events, rollbacks, db = setup_test(monkeypatch)
    request_body = make_request_body()

    def fail_service(**kwargs):
        raise ValueError("Synthetic repayment validation failure")

    monkeypatch.setattr(
        routes.repayment_service,
        "record_repayment",
        fail_service,
    )

    with pytest.raises(HTTPException) as exc_info:
        routes.record_repayment(
            request=request_body,
            api_request=make_request(),
            db=db,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Synthetic repayment validation failure"

    assert_event_sequence(events, ["started", "failed"])
    assert (
        events[-1]["error_code"]
        == "REPAYMENT_RECORDING_FAILED"
    )
    assert rollbacks == ["rollback"]


def test_record_repayment_unexpected_error_logs_failure_and_rolls_back(
    monkeypatch,
):
    events, rollbacks, db = setup_test(monkeypatch)

    def fail_service(**kwargs):
        raise RuntimeError("Synthetic repayment integration failure")

    monkeypatch.setattr(
        routes.repayment_service,
        "record_repayment",
        fail_service,
    )

    with pytest.raises(
        RuntimeError,
        match="Synthetic repayment integration failure",
    ):
        routes.record_repayment(
            request=make_request_body(),
            api_request=make_request(),
            db=db,
        )

    assert_event_sequence(events, ["started", "failed"])
    assert (
        events[-1]["error_code"]
        == "REPAYMENT_RECORDING_UNEXPECTED_FAILURE"
    )
    assert rollbacks == ["rollback"]