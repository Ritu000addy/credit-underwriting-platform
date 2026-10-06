from fastapi import Request

from backend.app.core.responses import (
    error_response,
    success_response,
)


def build_request(path: str) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": [],
        "query_string": b"",
        "server": ("testserver", 80),
        "scheme": "http",
    }

    request = Request(scope)
    request.state.request_id = "REQ-TEST-001"

    return request


def test_success_response_contract():
    request = build_request("/test")

    response = success_response(
        request=request,
        data={"id": "ABC001"},
        message="Test successful",
    )

    payload = response.model_dump(mode="json")

    assert payload["success"] is True
    assert payload["message"] == "Test successful"
    assert payload["data"] == {"id": "ABC001"}
    assert payload["error"] is None
    assert payload["meta"]["request_id"] == "REQ-TEST-001"
    assert payload["meta"]["path"] == "/test"
    assert payload["meta"]["timestamp"] is not None


def test_error_response_contract():
    request = build_request("/test")

    response = error_response(
        request=request,
        code="TEST_ERROR",
        message="Test failed",
        details={"field": "value"},
    )

    payload = response.model_dump(mode="json")

    assert payload["success"] is False
    assert payload["message"] == "Test failed"
    assert payload["data"] is None
    assert payload["error"]["code"] == "TEST_ERROR"
    assert payload["error"]["details"] == {
        "field": "value"
    }
    assert payload["meta"]["request_id"] == "REQ-TEST-001"
    assert payload["meta"]["path"] == "/test"