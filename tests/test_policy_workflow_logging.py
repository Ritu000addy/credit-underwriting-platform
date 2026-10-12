from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.app.api.routes import policy_version as routes


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
    request.state.request_id = "REQ-POLICY-LOG-TEST"
    return request


class FakeDB:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.refreshed = []

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def refresh(self, entity):
        self.refreshed.append(entity)


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
        "PolicyVersionResponse",
        SimpleNamespace(model_validate=lambda value: value),
    )

    return events, db


def assert_lifecycle(events, workflow, entity_id):
    assert [item["event"] for item in events] == [
        "started",
        "completed",
    ]
    assert all(item["workflow"] == workflow for item in events)
    assert all(item["entity_id"] == entity_id for item in events)


def test_policy_version_creation_logs_success(monkeypatch):
    events, db = setup_test(monkeypatch)

    result = SimpleNamespace(
        policy_version="POL-LOG-001",
        status="DRAFT",
    )
    monkeypatch.setattr(
        routes.policy_version_service,
        "create_policy_version",
        lambda **kwargs: result,
    )

    routes.create_policy_version(
        request=SimpleNamespace(
            policy_version="POL-LOG-001",
            effective_from=None,
            effective_to=None,
            policy_reference="TEST-REF",
            governance_notes="Synthetic test",
        ),
        api_request=make_request(),
        db=db,
    )

    assert_lifecycle(
        events, "policy_version_creation", "POL-LOG-001"
    )
    assert db.commits == 1
    assert db.rollbacks == 0


def test_policy_activation_logs_success(monkeypatch):
    events, db = setup_test(monkeypatch)

    result = SimpleNamespace(
        policy_version="POL-LOG-002",
        status="ACTIVE",
    )
    monkeypatch.setattr(
        routes.policy_version_service,
        "get_policy_version",
        lambda **kwargs: SimpleNamespace(status="DRAFT"),
    )
    monkeypatch.setattr(
        routes.policy_version_service,
        "activate_policy",
        lambda **kwargs: result,
    )

    routes.activate_policy_version(
        request=SimpleNamespace(
            policy_version="POL-LOG-002",
            actor_id="TEST-ACTOR",
        ),
        api_request=make_request(),
        db=db,
    )

    assert_lifecycle(
        events, "policy_version_activation", "POL-LOG-002"
    )
    assert db.commits == 1


def test_policy_deactivation_logs_success(monkeypatch):
    events, db = setup_test(monkeypatch)

    result = SimpleNamespace(
        policy_version="POL-LOG-003",
        status="INACTIVE",
    )
    monkeypatch.setattr(
        routes.policy_version_service,
        "get_policy_version",
        lambda **kwargs: SimpleNamespace(status="ACTIVE"),
    )
    monkeypatch.setattr(
        routes.policy_version_service,
        "deactivate_policy",
        lambda **kwargs: result,
    )

    routes.deactivate_policy_version(
        request=SimpleNamespace(
            policy_version="POL-LOG-003",
            actor_id="TEST-ACTOR",
        ),
        api_request=make_request(),
        db=db,
    )

    assert_lifecycle(
        events, "policy_version_deactivation", "POL-LOG-003"
    )
    assert db.commits == 1


def test_policy_rollback_logs_success(monkeypatch):
    events, db = setup_test(monkeypatch)

    result = SimpleNamespace(
        policy_version="POL-LOG-004",
        status="ACTIVE",
    )
    monkeypatch.setattr(
        routes.policy_version_service,
        "rollback_policy",
        lambda **kwargs: result,
    )

    routes.rollback_policy_version(
        request=SimpleNamespace(
            target_policy_version="POL-LOG-004",
            actor_id="TEST-ACTOR",
        ),
        api_request=make_request(),
        db=db,
    )

    assert_lifecycle(
        events, "policy_version_rollback", "POL-LOG-004"
    )
    assert db.commits == 1


def test_policy_retirement_logs_success(monkeypatch):
    events, db = setup_test(monkeypatch)

    result = SimpleNamespace(
        policy_version="POL-LOG-005",
        status="RETIRED",
    )
    monkeypatch.setattr(
        routes.policy_version_service,
        "get_policy_version",
        lambda **kwargs: SimpleNamespace(status="INACTIVE"),
    )
    monkeypatch.setattr(
        routes.policy_version_service,
        "retire_policy",
        lambda **kwargs: result,
    )

    routes.retire_policy_version(
        request=SimpleNamespace(
            policy_version="POL-LOG-005",
            actor_id="TEST-ACTOR",
        ),
        api_request=make_request(),
        db=db,
    )

    assert_lifecycle(
        events, "policy_version_retirement", "POL-LOG-005"
    )
    assert db.commits == 1


def test_policy_creation_failure_logs_and_rolls_back(monkeypatch):
    events, db = setup_test(monkeypatch)

    def fail_creation(**kwargs):
        raise ValueError("Synthetic policy validation failure")

    monkeypatch.setattr(
        routes.policy_version_service,
        "create_policy_version",
        fail_creation,
    )

    with pytest.raises(HTTPException) as exc_info:
        routes.create_policy_version(
            request=SimpleNamespace(
                policy_version="POL-LOG-FAIL",
                effective_from=None,
                effective_to=None,
                policy_reference="TEST-REF",
                governance_notes="Synthetic test",
            ),
            api_request=make_request(),
            db=db,
        )

    assert exc_info.value.status_code == 409
    assert [item["event"] for item in events] == [
        "started",
        "failed",
    ]
    assert events[-1]["workflow"] == "policy_version_creation"
    assert events[-1]["error_code"] == (
        "POLICY_VERSION_CREATION_REJECTED"
    )
    assert db.commits == 0
    assert db.rollbacks == 1