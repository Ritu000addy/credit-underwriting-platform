from types import SimpleNamespace

import pytest

from backend.app.core.security import get_current_user
from backend.app.main import app


@pytest.fixture
def operations_auth():
    previous_override = app.dependency_overrides.get(get_current_user)

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        username="test-operations",
        role="OPERATIONS",
    )

    try:
        yield
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = previous_override