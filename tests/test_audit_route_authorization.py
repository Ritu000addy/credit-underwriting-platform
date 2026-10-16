
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.app.core.security import get_current_user
from backend.app.main import app


client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def clear_auth_override():
    previous_override = app.dependency_overrides.pop(
        get_current_user, None
    )
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        if previous_override is not None:
            app.dependency_overrides[get_current_user] = previous_override


def test_audit_route_requires_authentication():
    response = client.get("/audit/AUTHZ-MISSING")

    assert response.status_code == 401


def test_audit_route_rejects_operations_role():
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        username="test-operations",
        role="OPERATIONS",
    )

    response = client.get("/audit/AUTHZ-MISSING")

    assert response.status_code == 403


def test_audit_route_allows_authorized_reader():
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        username="test-auditor",
        role="AUDITOR",
    )

    with patch(
        "backend.app.api.routes.audit.audit_log_service.get_by_application",
        return_value=[],
    ) as mock_get:
        response = client.get("/audit/AUTHZ-ALLOWED")

    assert response.status_code == 200
    mock_get.assert_called_once()
