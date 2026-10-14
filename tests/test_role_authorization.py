
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend.app.core.security import require_roles


def test_allowed_role_is_authorized():
    dependency = require_roles("CREDIT_OFFICER", "ADMIN")
    user = SimpleNamespace(role="CREDIT_OFFICER")

    assert dependency(current_user=user) is user


def test_admin_role_is_authorized():
    dependency = require_roles("CREDIT_OFFICER", "ADMIN")
    user = SimpleNamespace(role="ADMIN")

    assert dependency(current_user=user) is user


def test_role_comparison_is_case_insensitive():
    dependency = require_roles("credit_officer")
    user = SimpleNamespace(role="CREDIT_OFFICER")

    assert dependency(current_user=user) is user


def test_disallowed_role_receives_forbidden():
    dependency = require_roles("CREDIT_OFFICER", "ADMIN")
    user = SimpleNamespace(role="OPERATIONS")

    with pytest.raises(HTTPException) as exc_info:
        dependency(current_user=user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "INSUFFICIENT_ROLE"


def test_empty_allowed_roles_are_rejected():
    with pytest.raises(
        ValueError,
        match="AT_LEAST_ONE_ROLE_REQUIRED",
    ):
        require_roles()
