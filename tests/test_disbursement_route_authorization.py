from types import SimpleNamespace

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


def test_retry_requires_authentication():
    response = client.post("/disbursements/AUTHZ-MISSING/retry")

    assert response.status_code == 401


def test_retry_rejects_unauthorized_role():
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        username="test-analyst",
        role="CREDIT_ANALYST",
    )

    response = client.post("/disbursements/AUTHZ-MISSING/retry")

    assert response.status_code == 403


def test_disbursement_read_allows_operations_role():
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        username="test-operations",
        role="OPERATIONS",
    )

    response = client.get("/disbursements/AUTHZ-MISSING")

    # Authorization passes; the missing record should produce 404.
    assert response.status_code == 404