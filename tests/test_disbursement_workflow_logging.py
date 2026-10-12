from types import SimpleNamespace

import pytest
from starlette.requests import Request

from backend.app.api.routes import disbursements as disbursement_routes


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
    request.state.request_id = "REQ-DISBURSEMENT-TEST-001"
    return request


class FakeDB:
    def __init__(self, disbursement):
        self.disbursement = disbursement

    def get(self, model, disbursement_id):
        return self.disbursement


def capture_events(monkeypatch):
    events = []

    monkeypatch.setattr(
        disbursement_routes,
        "log_workflow_event",
        lambda **kwargs: events.append(kwargs),
    )
    monkeypatch.setattr(
        disbursement_routes,
        "success_response",
        lambda **kwargs: kwargs,
    )

    return events


def test_disbursement_status_update_logs_success(monkeypatch):
    events = capture_events(monkeypatch)

    disbursement = SimpleNamespace(
        disbursement_id="DISB-LOG-TEST-001",
        application_id="APP-LOG-TEST-001",
        status="CREATED",
    )

    monkeypatch.setattr(
        disbursement_routes.disbursement_service,
        "initiate_disbursement",
        lambda **kwargs: kwargs["disbursement"],
    )
    monkeypatch.setattr(
        disbursement_routes,
        "DisbursementResponse",
        SimpleNamespace(model_validate=lambda value: value),
    )

    result = disbursement_routes.update_disbursement_status(
        disbursement_id="DISB-LOG-TEST-001",
        update=SimpleNamespace(
            status="INITIATED",
            bank_reference=None,
            failure_reason=None,
        ),
        request=make_request(),
        db=FakeDB(disbursement),
    )

    assert result is not None
    assert [event["event"] for event in events] == [
        "started",
        "completed",
    ]
    assert all(
        event["workflow"] == "disbursement_status_update"
        for event in events
    )
    assert all(
        event["entity_id"] == "DISB-LOG-TEST-001"
        for event in events
    )


def test_disbursement_retry_logs_success(monkeypatch):
    events = capture_events(monkeypatch)

    monkeypatch.setattr(
        disbursement_routes.disbursement_retry_service,
        "retry_disbursement",
        lambda **kwargs: {"status": "RETRY_PROCESSED"},
    )

    result = disbursement_routes.retry_disbursement(
        disbursement_id="DISB-LOG-TEST-002",
        request=make_request(),
        db=None,
    )

    assert result is not None
    assert [event["event"] for event in events] == [
        "started",
        "completed",
    ]
    assert all(
        event["workflow"] == "disbursement_retry"
        for event in events
    )


def test_disbursement_retry_logs_unexpected_failure(monkeypatch):
    events = capture_events(monkeypatch)

    def fail_retry(**kwargs):
        raise RuntimeError("Synthetic retry failure")

    monkeypatch.setattr(
        disbursement_routes.disbursement_retry_service,
        "retry_disbursement",
        fail_retry,
    )

    with pytest.raises(RuntimeError, match="Synthetic retry failure"):
        disbursement_routes.retry_disbursement(
            disbursement_id="DISB-LOG-TEST-003",
            request=make_request(),
            db=None,
        )

    assert [event["event"] for event in events] == [
        "started",
        "failed",
    ]
    assert events[-1]["error_code"] == "DISBURSEMENT_RETRY_FAILED"