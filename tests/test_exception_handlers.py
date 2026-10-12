import asyncio
import json

import pytest
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from backend.app.core.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)


def make_request(path: str = "/test") -> Request:
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": [],
            "client": ("testclient", 123),
            "server": ("testserver", 80),
        }
    )


def run_handler(coroutine):
    return asyncio.run(coroutine)


def test_business_rule_error_preserves_domain_code():
    response = run_handler(
        http_exception_handler(
            make_request("/customer-communications/decision-draft"),
            StarletteHTTPException(
                status_code=422,
                detail="APPROVAL_DRAFT_REQUIRES_APPROVE_DECISION",
            ),
        )
    )

    payload = json.loads(response.body)

    assert response.status_code == 422
    assert payload["success"] is False
    assert (
        payload["error"]["code"]
        == "APPROVAL_DRAFT_REQUIRES_APPROVE_DECISION"
    )
    assert payload["meta"]["path"] == (
        "/customer-communications/decision-draft"
    )


@pytest.mark.parametrize(
    ("status_code", "expected_code"),
    [
        (401, "AUTHENTICATION_REQUIRED"),
        (403, "ACCESS_FORBIDDEN"),
        (404, "RESOURCE_NOT_FOUND"),
        (409, "RESOURCE_CONFLICT"),
        (502, "UPSTREAM_PROVIDER_ERROR"),
    ],
)
def test_http_status_uses_standard_error_code(
    status_code: int,
    expected_code: str,
):
    response = run_handler(
        http_exception_handler(
            make_request(),
            StarletteHTTPException(
                status_code=status_code,
                detail="Request failed.",
            ),
        )
    )

    payload = json.loads(response.body)

    assert response.status_code == status_code
    assert payload["error"]["code"] == expected_code
    assert payload["meta"]["request_id"]


def test_genai_structured_response_error_code_is_preserved():
    response = run_handler(
        http_exception_handler(
            make_request("/genai-underwriting/analyze"),
            StarletteHTTPException(
                status_code=502,
                detail=(
                    "The GenAI provider returned an invalid "
                    "structured response."
                ),
            ),
        )
    )

    payload = json.loads(response.body)

    assert response.status_code == 502
    assert payload["error"]["code"] == (
        "GENAI_INVALID_STRUCTURED_RESPONSE"
    )


def test_validation_response_does_not_echo_input_value():
    sensitive_value = "SYNTHETIC-SENSITIVE-VALUE"

    exc = RequestValidationError(
        [
            {
                "loc": ("body", "customer_id"),
                "msg": "Invalid value.",
                "type": "value_error",
                "input": sensitive_value,
            }
        ]
    )

    response = run_handler(
        request_validation_exception_handler(
            make_request("/test"),
            exc,
        )
    )

    payload = json.loads(response.body)
    serialized_response = response.body.decode()

    assert response.status_code == 422
    assert payload["error"]["code"] == "REQUEST_VALIDATION_ERROR"
    assert sensitive_value not in serialized_response

    detail = payload["error"]["details"][0]
    assert detail["loc"] == ["body", "customer_id"]
    assert detail["msg"] == "Invalid value."
    assert detail["type"] == "value_error"
    assert "input" not in detail