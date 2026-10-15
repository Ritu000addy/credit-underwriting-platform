from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.app.api.routes import sanctions as routes


def make_request():
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/sanctions",
        "raw_path": b"/sanctions",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 123),
        "server": ("testserver", 80),
    }

    request = Request(scope)
    request.state.request_id = "REQ-SANCTION-LOG-TEST"
    return request


def make_sanction_request():
    return SimpleNamespace(
        application_id="APP-SANCTION-LOG-001",
        sanctioned_amount="150000.00",
        sanctioned_tenure=12,
        sanctioned_emi="13327.32",
        interest_rate="12.0000",
        approval_authority="TEST",
        terms_and_conditions="Synthetic test terms",
        expires_at=None,
    )


def setup_test(monkeypatch):
    events = []
    rollbacks = []

    commits = []

    db = SimpleNamespace(
        commit=lambda: commits.append("commit"),
        rollback=lambda: rollbacks.append("rollback"),
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
        "SanctionResponse",
        SimpleNamespace(model_validate=lambda value: value),
    )

    return events, rollbacks, commits, db


def test_create_sanction_logs_success(monkeypatch):
    events, rollbacks, commits, db = setup_test(monkeypatch)
    request_body = make_sanction_request()

    sanction_result = SimpleNamespace(
        sanction_id="SAN-LOG-001",
        application_id=request_body.application_id,
        sanction_status="APPROVED",
    )    

    created_sanction_ids = []
    created_results = []

    def fake_create_sanction(**kwargs):
        assert kwargs["db"] is db
        assert kwargs["application_id"] == request_body.application_id

        result = SimpleNamespace(
            sanction_id=kwargs["sanction_id"],
            application_id=kwargs["application_id"],
            sanction_status="APPROVED",
        )
        created_sanction_ids.append(kwargs["sanction_id"])
        created_results.append(result)
        return result

    monkeypatch.setattr(
        routes.sanction_service,
        "create_sanction",
        fake_create_sanction,
    )

    response = routes.create_sanction(
        sanction=request_body,
        request=make_request(),
        db=db,
    )

    assert [event["event"] for event in events] == [
        "started",
        "completed",
    ]
    assert all(
        event["workflow"] == "sanction_creation"
        for event in events
    )
    assert all(
        event["application_id"] == request_body.application_id
        for event in events
    )
    assert created_sanction_ids
    assert all(
        event["entity_id"] == created_sanction_ids[0]
        for event in events
    )
    assert events[-1]["status"] == "APPROVED"
    assert response["data"] is created_results[0]
    assert rollbacks == []

    assert commits == ["commit"]

    # Do not expose sanction amounts or terms in workflow metadata.
    for event in events:
        assert "sanctioned_amount" not in event
        assert "sanctioned_emi" not in event
        assert "terms_and_conditions" not in event


def test_create_sanction_failure_logs_and_rolls_back(monkeypatch):
    events, rollbacks, commits, db = setup_test(monkeypatch)
    request_body = make_sanction_request()

    def fail_create_sanction(**kwargs):
        raise RuntimeError("Synthetic sanction service failure")

    monkeypatch.setattr(
        routes.sanction_service,
        "create_sanction",
        fail_create_sanction,
    )

    with pytest.raises(HTTPException) as exc_info:
        routes.create_sanction(
            sanction=request_body,
            request=make_request(),
            db=db,
        )

    # Preserve the route's currently implemented exception mapping.
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Synthetic sanction service failure"

    assert [event["event"] for event in events] == [
        "started",
        "failed",
    ]
    assert all(
        event["workflow"] == "sanction_creation"
        for event in events
    )
    assert events[-1]["error_code"] == "SANCTION_CREATION_FAILED"
    assert rollbacks == ["rollback"]