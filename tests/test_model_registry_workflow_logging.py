from types import SimpleNamespace

from starlette.requests import Request

from backend.app.api.routes import model_registry as routes


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
    request.state.request_id = "REQ-MODEL-GOVERNANCE-TEST"
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
        "ModelRegistryResponse",
        SimpleNamespace(model_validate=lambda value: value),
    )

    return events, db


def assert_success(events, workflow, entity_id):
    assert [item["event"] for item in events] == [
        "started",
        "completed",
    ]
    assert all(item["workflow"] == workflow for item in events)
    assert all(item["entity_id"] == entity_id for item in events)


def test_register_model_logs_success(monkeypatch):
    events, db = setup_test(monkeypatch)

    result = SimpleNamespace(
        model_registry_id="MR-LOG-001",
        model_name="TEST_MODEL",
        model_version="1.0",
        lifecycle_status="REGISTERED",
    )
    monkeypatch.setattr(
        routes.model_registry_service,
        "register_model",
        lambda **kwargs: result,
    )

    request_body = SimpleNamespace(
        model_registry_id="MR-LOG-001",
        model_name="TEST_MODEL",
        model_version="1.0",
        deployment_status="INACTIVE",
        model_type="CLASSIFICATION",
        training_data_version="DATA-1",
        training_date=None,
        roc_auc=None,
        model_metrics={},
        environment="TEST",
        model_reference="TEST-REF",
        governance_notes="Synthetic test",
    )

    routes.register_model(
        request=request_body,
        api_request=make_request(),
        db=db,
    )

    assert_success(events, "model_registration", "MR-LOG-001")
    assert db.commits == 1
    assert db.rollbacks == 0


def test_start_model_validation_logs_success(monkeypatch):
    events, db = setup_test(monkeypatch)

    model = SimpleNamespace(
        model_registry_id="MR-LOG-002",
        model_name="TEST_MODEL",
        model_version="1.0",
        lifecycle_status="REGISTERED",
    )
    result = SimpleNamespace(
        model_registry_id="MR-LOG-002",
        model_version="1.0",
        lifecycle_status="VALIDATION",
    )

    monkeypatch.setattr(
        routes.model_registry_service,
        "get_model",
        lambda **kwargs: model,
    )
    monkeypatch.setattr(
        routes.model_registry_service,
        "start_validation",
        lambda **kwargs: result,
    )

    routes.start_model_validation(
        request=SimpleNamespace(
            model_name="TEST_MODEL",
            model_version="1.0",
        ),
        api_request=make_request(),
        db=db,
    )

    assert_success(
        events, "model_validation_start", "TEST_MODEL:1.0"
    )
    assert db.commits == 1


def test_complete_model_validation_logs_success(monkeypatch):
    events, db = setup_test(monkeypatch)

    model = SimpleNamespace(
        model_registry_id="MR-LOG-003",
        model_name="TEST_MODEL",
        model_version="1.0",
    )
    result = SimpleNamespace(
        model_registry_id="MR-LOG-003",
        model_version="1.0",
        validation_status="PASSED",
        lifecycle_status="VALIDATED",
    )

    monkeypatch.setattr(
        routes.model_registry_service,
        "get_model",
        lambda **kwargs: model,
    )
    monkeypatch.setattr(
        routes.model_registry_service,
        "complete_validation",
        lambda **kwargs: result,
    )

    routes.complete_model_validation(
        request=SimpleNamespace(
            model_name="TEST_MODEL",
            model_version="1.0",
            passed=True,
            validated_by="TEST-REVIEWER",
            validation_notes="Synthetic test",
        ),
        api_request=make_request(),
        db=db,
    )

    assert_success(
        events, "model_validation_completion", "TEST_MODEL:1.0"
    )
    assert db.commits == 1


def test_approve_model_logs_success(monkeypatch):
    events, db = setup_test(monkeypatch)

    model = SimpleNamespace(lifecycle_status="VALIDATED")
    result = SimpleNamespace(
        model_registry_id="MR-LOG-004",
        model_version="1.0",
        lifecycle_status="APPROVED",
    )

    monkeypatch.setattr(
        routes.model_registry_service,
        "get_model",
        lambda **kwargs: model,
    )
    monkeypatch.setattr(
        routes.model_registry_service,
        "approve_model",
        lambda **kwargs: result,
    )

    routes.approve_model(
        request=SimpleNamespace(
            model_name="TEST_MODEL",
            model_version="1.0",
            approved_by="TEST-APPROVER",
        ),
        api_request=make_request(),
        db=db,
    )

    assert_success(events, "model_approval", "TEST_MODEL:1.0")
    assert db.commits == 1


def test_activate_model_logs_success(monkeypatch):
    events, db = setup_test(monkeypatch)

    model = SimpleNamespace(lifecycle_status="APPROVED")
    result = SimpleNamespace(
        model_registry_id="MR-LOG-005",
        model_version="1.0",
        lifecycle_status="ACTIVE",
    )

    monkeypatch.setattr(
        routes.model_registry_service,
        "get_model",
        lambda **kwargs: model,
    )
    monkeypatch.setattr(
        routes.model_registry_service,
        "activate_model",
        lambda **kwargs: result,
    )

    routes.activate_model(
        request=SimpleNamespace(
            model_name="TEST_MODEL",
            model_version="1.0",
        ),
        api_request=make_request(),
        db=db,
    )

    assert_success(events, "model_activation", "TEST_MODEL:1.0")
    assert db.commits == 1


def test_deactivate_model_logs_success(monkeypatch):
    events, db = setup_test(monkeypatch)

    model = SimpleNamespace(lifecycle_status="ACTIVE")
    result = SimpleNamespace(
        model_registry_id="MR-LOG-006",
        model_version="1.0",
        lifecycle_status="INACTIVE",
    )

    monkeypatch.setattr(
        routes.model_registry_service,
        "get_model",
        lambda **kwargs: model,
    )
    monkeypatch.setattr(
        routes.model_registry_service,
        "deactivate_model",
        lambda **kwargs: result,
    )

    routes.deactivate_model(
        request=SimpleNamespace(
            model_name="TEST_MODEL",
            model_version="1.0",
        ),
        api_request=make_request(),
        db=db,
    )

    assert_success(events, "model_deactivation", "TEST_MODEL:1.0")
    assert db.commits == 1


def test_rollback_model_logs_success(monkeypatch):
    events, db = setup_test(monkeypatch)

    current_model = SimpleNamespace(
        model_registry_id="MR-CURRENT",
        lifecycle_status="ACTIVE",
    )
    prior_model = SimpleNamespace(
        model_registry_id="MR-PRIOR",
        lifecycle_status="INACTIVE",
    )
    result = SimpleNamespace(
        model_registry_id="MR-LOG-007",
        model_version="1.0",
        lifecycle_status="ACTIVE",
    )

    def get_model(**kwargs):
        if kwargs["model_version"] == "2.0":
            return current_model
        return prior_model

    monkeypatch.setattr(
        routes.model_registry_service,
        "get_model",
        get_model,
    )
    monkeypatch.setattr(
        routes.model_registry_service,
        "rollback_model",
        lambda **kwargs: result,
    )

    routes.rollback_model(
        request=SimpleNamespace(
            model_name="TEST_MODEL",
            current_version="2.0",
            rollback_version="1.0",
        ),
        api_request=make_request(),
        db=db,
    )

    assert_success(events, "model_rollback", "TEST_MODEL:2.0->1.0")
    assert db.commits == 1