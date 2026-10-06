from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_underwriting_invalid_request_returns_422():
    response = client.post(
        "/underwriting/evaluate",
        json={
            "application": "INVALID_APPLICATION",
            "borrower": {},
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["error"]["code"] == "REQUEST_VALIDATION_ERROR"
    assert "request_id" in body
    assert body["path"] == "/underwriting/evaluate"


def test_underwriting_missing_request_body_returns_422():
    response = client.post(
        "/underwriting/evaluate",
    )

    assert response.status_code == 422

    body = response.json()

    assert body["error"]["code"] == "REQUEST_VALIDATION_ERROR"
    assert "request_id" in body