from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.app.api.routes import auth as routes


def make_request():
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/auth/login",
        "raw_path": b"/auth/login",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 123),
        "server": ("testserver", 80),
    }
    request = Request(scope)
    request.state.request_id = "REQ-AUTH-LOG-TEST"
    return request


def setup_test(monkeypatch):
    events = []
    commits = []
    rollbacks = []

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

    return events, commits, rollbacks, db


def test_login_success_logs_completed_without_secrets(monkeypatch):
    events, commits, rollbacks, db = setup_test(monkeypatch)

    user = SimpleNamespace(
        user_id="USER-AUTH-001",
        last_login_at=None,
    )
    monkeypatch.setattr(
        routes.auth_user_service,
        "authenticate_user",
        lambda **kwargs: user,
    )
    monkeypatch.setattr(
        routes,
        "create_access_token",
        lambda **kwargs: "TEST-ACCESS-TOKEN",
    )

    response = routes.login(
        form_data=SimpleNamespace(
            username="test-user",
            password="Synthetic-Password-123",
        ),
        request=make_request(),
        db=db,
    )

    assert [event["event"] for event in events] == [
        "started",
        "completed",
    ]
    assert all(
        event["workflow"] == "authentication_login"
        for event in events
    )
    assert events[-1]["entity_id"] == "USER-AUTH-001"
    assert events[-1]["status"] == "SUCCESS"
    assert response["data"].access_token == "TEST-ACCESS-TOKEN"
    assert commits == ["commit"]
    assert rollbacks == []

    event_text = repr(events)
    assert "Synthetic-Password-123" not in event_text
    assert "TEST-ACCESS-TOKEN" not in event_text
    assert "test-user" not in event_text


def test_login_invalid_credentials_logs_failure(monkeypatch):
    events, commits, rollbacks, db = setup_test(monkeypatch)

    monkeypatch.setattr(
        routes.auth_user_service,
        "authenticate_user",
        lambda **kwargs: None,
    )

    with pytest.raises(HTTPException) as exc_info:
        routes.login(
            form_data=SimpleNamespace(
                username="unknown-user",
                password="Synthetic-Password-456",
            ),
            request=make_request(),
            db=db,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "INVALID_USERNAME_OR_PASSWORD"
    assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"

    assert [event["event"] for event in events] == [
        "started",
        "failed",
    ]
    assert events[-1]["error_code"] == "INVALID_USERNAME_OR_PASSWORD"
    assert commits == []
    assert rollbacks == []

    event_text = repr(events)
    assert "Synthetic-Password-456" not in event_text
    assert "unknown-user" not in event_text


def test_login_unexpected_failure_logs_and_rolls_back(monkeypatch):
    events, commits, rollbacks, db = setup_test(monkeypatch)

    def fail_authentication(**kwargs):
        raise RuntimeError("Synthetic authentication failure")

    monkeypatch.setattr(
        routes.auth_user_service,
        "authenticate_user",
        fail_authentication,
    )

    with pytest.raises(
        RuntimeError,
        match="Synthetic authentication failure",
    ):
        routes.login(
            form_data=SimpleNamespace(
                username="test-user",
                password="Synthetic-Password-789",
            ),
            request=make_request(),
            db=db,
        )

    assert [event["event"] for event in events] == [
        "started",
        "failed",
    ]
    assert events[-1]["error_code"] == "LOGIN_PROCESSING_FAILED"
    assert commits == []
    assert rollbacks == ["rollback"]

    event_text = repr(events)
    assert "Synthetic-Password-789" not in event_text