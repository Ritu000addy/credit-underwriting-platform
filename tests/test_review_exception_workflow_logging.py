from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.app.api.routes import review_exception as routes


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
    request.state.request_id = "REQ-REVIEW-EXCEPTION-TEST"
    return request


class FakeDB:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def refresh(self, entity):
        pass


def setup_test(monkeypatch):
    events = []
    db = FakeDB()

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
        routes.audit_log_service,
        "log",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        routes,
        "ReviewExceptionResponse",
        SimpleNamespace(
            model_validate=lambda value, **kwargs: value
        ),
    )

    return events, db


def assert_success(events, workflow, entity_id):
    assert [item["event"] for item in events] == [
        "started",
        "completed",
    ]
    assert all(item["workflow"] == workflow for item in events)
    assert all(item["entity_id"] == entity_id for item in events)


def make_exception(exception_id, status="OPEN"):
    return SimpleNamespace(
        exception_id=exception_id,
        application_id="APP-EXCEPTION-TEST",
        status=status,
    )


def test_create_review_exception_logs_success(monkeypatch):
    events, db = setup_test(monkeypatch)

    result = SimpleNamespace(
        exception_id="EXC-TEST-001",
        application_id="APP-EXCEPTION-TEST",
        status="OPEN",
    )

    monkeypatch.setattr(
        routes.review_exception_service,
        "create_exception",
        lambda **kwargs: result,
    )

    routes.create_review_exception(
        request=SimpleNamespace(
            review_id="REVIEW-TEST-001",
            application_id="APP-EXCEPTION-TEST",
            exception_type="POLICY",
            description="Synthetic test exception",
            created_by="TEST-USER",
        ),
        api_request=make_request(),
        db=db,
    )

    assert_success(
        events, "review_exception_creation", "REVIEW-TEST-001"
    )
    assert db.commits == 1
    assert db.rollbacks == 0


def test_assign_review_exception_logs_success(monkeypatch):
    events, db = setup_test(monkeypatch)
    exception_id = "EXC-TEST-002"
    exception = make_exception(exception_id)
    result = make_exception(exception_id, status="ASSIGNED")

    monkeypatch.setattr(
        routes.review_exception_service,
        "get_exception",
        lambda **kwargs: exception,
    )
    monkeypatch.setattr(
        routes.review_exception_service,
        "assign_exception",
        lambda **kwargs: result,
    )

    routes.assign_review_exception(
        exception_id=exception_id,
        request=SimpleNamespace(assigned_to="TEST-REVIEWER"),
        api_request=make_request(),
        db=db,
    )

    assert_success(
        events, "review_exception_assignment", exception_id
    )
    assert db.commits == 1


def test_request_exception_information_logs_success(monkeypatch):
    events, db = setup_test(monkeypatch)
    exception_id = "EXC-TEST-003"
    exception = make_exception(exception_id)
    result = make_exception(exception_id, status="AWAITING_INFORMATION")

    monkeypatch.setattr(
        routes.review_exception_service,
        "get_exception",
        lambda **kwargs: exception,
    )
    monkeypatch.setattr(
        routes.review_exception_service,
        "request_information",
        lambda **kwargs: result,
    )

    routes.request_exception_information(
        exception_id=exception_id,
        request=SimpleNamespace(
            requested_information="Synthetic missing document",
            actor_id="TEST-REVIEWER",
        ),
        api_request=make_request(),
        db=db,
    )

    assert_success(
        events, "review_exception_information_request", exception_id
    )
    assert db.commits == 1


def test_resume_review_exception_logs_success(monkeypatch):
    events, db = setup_test(monkeypatch)
    exception_id = "EXC-TEST-004"
    exception = make_exception(exception_id, status="AWAITING_INFORMATION")
    result = make_exception(exception_id, status="OPEN")

    monkeypatch.setattr(
        routes.review_exception_service,
        "get_exception",
        lambda **kwargs: exception,
    )
    monkeypatch.setattr(
        routes.review_exception_service,
        "resume_from_information",
        lambda **kwargs: result,
    )

    routes.resume_review_exception(
        exception_id=exception_id,
        request=SimpleNamespace(actor_id="TEST-REVIEWER"),
        api_request=make_request(),
        db=db,
    )

    assert_success(
        events, "review_exception_resume", exception_id
    )
    assert db.commits == 1


def test_resolve_review_exception_logs_success(monkeypatch):
    events, db = setup_test(monkeypatch)
    exception_id = "EXC-TEST-005"
    exception = make_exception(exception_id)
    result = make_exception(exception_id, status="RESOLVED")

    monkeypatch.setattr(
        routes.review_exception_service,
        "get_exception",
        lambda **kwargs: exception,
    )
    monkeypatch.setattr(
        routes.review_exception_service,
        "resolve_exception",
        lambda **kwargs: result,
    )

    routes.resolve_review_exception(
        exception_id=exception_id,
        request=SimpleNamespace(
            resolution_action="ACCEPT",
            resolution_remarks="Synthetic resolution",
            resolved_by="TEST-REVIEWER",
        ),
        api_request=make_request(),
        db=db,
    )

    assert_success(
        events, "review_exception_resolution", exception_id
    )
    assert db.commits == 1


def test_close_review_exception_logs_success(monkeypatch):
    events, db = setup_test(monkeypatch)
    exception_id = "EXC-TEST-006"
    exception = make_exception(exception_id, status="RESOLVED")
    result = make_exception(exception_id, status="CLOSED")

    monkeypatch.setattr(
        routes.review_exception_service,
        "get_exception",
        lambda **kwargs: exception,
    )
    monkeypatch.setattr(
        routes.review_exception_service,
        "close_exception",
        lambda **kwargs: result,
    )

    routes.close_review_exception(
        exception_id=exception_id,
        request=SimpleNamespace(actor_id="TEST-REVIEWER"),
        api_request=make_request(),
        db=db,
    )

    assert_success(
        events, "review_exception_closure", exception_id
    )
    assert db.commits == 1


def test_create_review_exception_logs_failure_and_rolls_back(
    monkeypatch,
):
    events, db = setup_test(monkeypatch)

    def fail_creation(**kwargs):
        raise ValueError("Synthetic validation failure")

    monkeypatch.setattr(
        routes.review_exception_service,
        "create_exception",
        fail_creation,
    )

    with pytest.raises(HTTPException) as exc_info:
        routes.create_review_exception(
            request=SimpleNamespace(
                review_id="REVIEW-TEST-FAIL",
                application_id="APP-EXCEPTION-TEST",
                exception_type="POLICY",
                description="Synthetic test exception",
                created_by="TEST-USER",
            ),
            api_request=make_request(),
            db=db,
        )

    assert exc_info.value.status_code == 409
    assert [item["event"] for item in events] == [
        "started",
        "failed",
    ]
    assert events[-1]["workflow"] == "review_exception_creation"
    assert events[-1]["error_code"] == (
        "REVIEW_EXCEPTION_CREATION_REJECTED"
    )
    assert db.commits == 0
    assert db.rollbacks == 1