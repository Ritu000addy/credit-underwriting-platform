from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.app.api.routes import operations as routes


def make_request():
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/test",
        "raw_path": b"/test",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 123),
        "server": ("testserver", 80),
    }
    request = Request(scope)
    request.state.request_id = "REQ-OPS-QUEUE-TEST"
    return request


def setup_test(monkeypatch):
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

    return events


def call_update():
    return routes.update_operations_queue_status(
        queue_id="QUEUE-TEST-001",
        queue_status="RESOLVED",
        request=make_request(),
        db=None,
    )


def test_operations_queue_update_logs_success(monkeypatch):
    events = setup_test(monkeypatch)

    result = SimpleNamespace(
        queue_id="QUEUE-TEST-001",
        reconciliation_id="RECON-TEST-001",
        disbursement_id="DISB-TEST-001",
        queue_type="RECONCILIATION",
        queue_status="RESOLVED",
        reason="Synthetic test",
    )

    monkeypatch.setattr(
        routes.reconciliation_service,
        "update_operations_queue_status",
        lambda **kwargs: result,
    )

    response = call_update()

    assert response is not None
    assert [event["event"] for event in events] == [
        "started",
        "completed",
    ]
    assert all(
        event["workflow"] == "operations_queue_status_update"
        for event in events
    )
    assert all(
        event["entity_id"] == "QUEUE-TEST-001"
        for event in events
    )
    assert events[-1]["status"] == "RESOLVED"


@pytest.mark.parametrize(
    ("service_error", "expected_status", "expected_code"),
    [
        (
            "OPERATIONS_QUEUE_NOT_FOUND",
            404,
            "OPERATIONS_QUEUE_NOT_FOUND",
        ),
        (
            "INVALID_OPERATIONS_QUEUE_STATUS",
            400,
            "INVALID_OPERATIONS_QUEUE_STATUS",
        ),
        (
            "OPERATIONS_QUEUE_ALREADY_RESOLVED",
            400,
            "OPERATIONS_QUEUE_ALREADY_RESOLVED",
        ),
    ],
)
def test_operations_queue_business_errors_are_logged(
    monkeypatch,
    service_error,
    expected_status,
    expected_code,
):
    events = setup_test(monkeypatch)

    def raise_service_error(**kwargs):
        raise ValueError(service_error)

    monkeypatch.setattr(
        routes.reconciliation_service,
        "update_operations_queue_status",
        raise_service_error,
    )

    with pytest.raises(HTTPException) as exc_info:
        call_update()

    assert exc_info.value.status_code == expected_status
    assert [event["event"] for event in events] == [
        "started",
        "failed",
    ]
    assert events[-1]["error_code"] == expected_code
    assert events[-1]["entity_id"] == "QUEUE-TEST-001"


def test_operations_queue_unexpected_failure_is_logged(monkeypatch):
    events = setup_test(monkeypatch)

    def raise_unexpected_error(**kwargs):
        raise RuntimeError("Synthetic operations failure")

    monkeypatch.setattr(
        routes.reconciliation_service,
        "update_operations_queue_status",
        raise_unexpected_error,
    )

    with pytest.raises(
        RuntimeError,
        match="Synthetic operations failure",
    ):
        call_update()

    assert [event["event"] for event in events] == [
        "started",
        "failed",
    ]
    assert events[-1]["error_code"] == (
        "OPERATIONS_QUEUE_STATUS_UPDATE_FAILED"
    )