import logging

from starlette.requests import Request

from backend.app.core.workflow_logging import log_workflow_event


def make_request() -> Request:
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
    request.state.request_id = "REQ-WORKFLOW-TEST-001"
    return request


def test_workflow_started_event_is_logged(caplog):
    request = make_request()

    with caplog.at_level(logging.INFO, logger="backend.workflow"):
        log_workflow_event(
            workflow="sanction_creation",
            event="started",
            request=request,
            application_id="APP-WORKFLOW-TEST-001",
            entity_type="sanction",
            entity_id="SAN-WORKFLOW-TEST-001",
        )

    assert "workflow_event" in caplog.text
    assert "REQ-WORKFLOW-TEST-001" in caplog.text
    assert "sanction_creation" in caplog.text
    assert "event=started" in caplog.text


def test_workflow_failure_event_is_logged(caplog):
    request = make_request()

    with caplog.at_level(logging.WARNING, logger="backend.workflow"):
        log_workflow_event(
            workflow="repayment_recording",
            event="failed",
            request=request,
            entity_type="repayment",
            error_code="REPAYMENT_RECORDING_FAILED",
        )

    assert "REQ-WORKFLOW-TEST-001" in caplog.text
    assert "repayment_recording" in caplog.text
    assert "event=failed" in caplog.text
    assert "REPAYMENT_RECORDING_FAILED" in caplog.text