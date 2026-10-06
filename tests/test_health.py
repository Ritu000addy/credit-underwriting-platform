import logging

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_check_reports_database_healthy():
    response = client.get("/health")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "healthy"
    assert payload["database"] == "healthy"
    assert payload["service"] == "AI Credit Underwriting Platform"
    assert payload["version"] == "0.1.0"


def test_http_request_access_log(caplog):
    with caplog.at_level(
        logging.INFO,
        logger="backend.http",
    ):
        response = client.get("/health")

    assert response.status_code == 200

    assert "request_completed" in caplog.text
    assert "request_id=REQ-" in caplog.text
    assert "method=GET" in caplog.text
    assert "path=/health" in caplog.text
    assert "status_code=200" in caplog.text
    assert "duration_ms=" in caplog.text