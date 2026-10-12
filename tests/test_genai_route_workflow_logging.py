from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.app.api.routes import genai_underwriting as genai_routes
from backend.app.api.routes import customer_communications as comm_routes


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
    request.state.request_id = "REQ-GENAI-LOG-TEST"
    return request


def setup_test(monkeypatch, module):
    events = []

    monkeypatch.setattr(
        module,
        "log_workflow_event",
        lambda **kwargs: events.append(kwargs),
    )
    monkeypatch.setattr(
        module,
        "success_response",
        lambda **kwargs: kwargs,
    )

    return events


def assert_lifecycle(events, workflow, application_id, outcome):
    assert [event["event"] for event in events] == [
        "started",
        outcome,
    ]
    assert all(event["workflow"] == workflow for event in events)
    assert all(
        event["entity_id"] == application_id
        for event in events
    )


def make_borrower_and_underwriting():
    borrower = SimpleNamespace(customer_id="CUST-GENAI-001")
    underwriting = SimpleNamespace(
        customer_id="CUST-GENAI-001",
        application_id="APP-GENAI-001",
    )
    return borrower, underwriting


def test_analyze_underwriting_logs_success(monkeypatch):
    events = setup_test(monkeypatch, genai_routes)
    borrower, underwriting = make_borrower_and_underwriting()

    monkeypatch.setattr(
        genai_routes,
        "GenAIUnderwritingResult",
        SimpleNamespace(model_validate=lambda value: value),
    )
    monkeypatch.setattr(
        genai_routes.genai_underwriting_service,
        "generate",
        lambda **kwargs: SimpleNamespace(status="COMPLETED"),
    )

    genai_routes.analyze_underwriting(
        borrower=borrower,
        underwriting=underwriting,
        request=make_request(),
    )

    assert_lifecycle(
        events,
        "genai_underwriting_analysis",
        "APP-GENAI-001",
        "completed",
    )


def test_analyze_underwriting_logs_validation_failure(monkeypatch):
    events = setup_test(monkeypatch, genai_routes)
    borrower, underwriting = make_borrower_and_underwriting()

    def fail_generation(**kwargs):
        raise ValueError("Synthetic validation failure")

    monkeypatch.setattr(
        genai_routes.genai_underwriting_service,
        "generate",
        fail_generation,
    )

    with pytest.raises(HTTPException) as exc_info:
        genai_routes.analyze_underwriting(
            borrower=borrower,
            underwriting=underwriting,
            request=make_request(),
        )

    assert exc_info.value.status_code == 422
    assert_lifecycle(
        events,
        "genai_underwriting_analysis",
        "APP-GENAI-001",
        "failed",
    )
    assert events[-1]["error_code"] == (
        "GENAI_UNDERWRITING_VALIDATION_FAILED"
    )


def test_generate_underwriting_report_logs_success(monkeypatch):
    events = setup_test(monkeypatch, genai_routes)
    borrower, underwriting = make_borrower_and_underwriting()

    monkeypatch.setattr(
        genai_routes.genai_underwriting_service,
        "generate",
        lambda **kwargs: SimpleNamespace(status="COMPLETED"),
    )
    monkeypatch.setattr(
        genai_routes.underwriting_report_service,
        "generate",
        lambda **kwargs: SimpleNamespace(
            application_id="APP-GENAI-001"
        ),
    )

    genai_routes.generate_underwriting_report(
        borrower=borrower,
        underwriting=underwriting,
        request=make_request(),
    )

    assert_lifecycle(
        events,
        "underwriting_report_generation",
        "APP-GENAI-001",
        "completed",
    )


def test_generate_underwriting_report_logs_failure(monkeypatch):
    events = setup_test(monkeypatch, genai_routes)
    borrower, underwriting = make_borrower_and_underwriting()

    def fail_generation(**kwargs):
        raise ValueError("Synthetic report validation failure")

    monkeypatch.setattr(
        genai_routes.genai_underwriting_service,
        "generate",
        fail_generation,
    )

    with pytest.raises(HTTPException) as exc_info:
        genai_routes.generate_underwriting_report(
            borrower=borrower,
            underwriting=underwriting,
            request=make_request(),
        )

    assert exc_info.value.status_code == 422
    assert_lifecycle(
        events,
        "underwriting_report_generation",
        "APP-GENAI-001",
        "failed",
    )
    assert events[-1]["error_code"] == (
        "UNDERWRITING_REPORT_GENERATION_REJECTED"
    )


def test_markdown_export_logs_success(monkeypatch):
    events = setup_test(monkeypatch, genai_routes)

    monkeypatch.setattr(
        genai_routes.underwriting_report_service,
        "to_markdown",
        lambda report: "# Synthetic internal report",
    )

    response = genai_routes.export_underwriting_report_markdown(
        report=SimpleNamespace(application_id="APP-GENAI-003"),
        request=make_request(),
    )

    assert response.media_type == "text/markdown"
    assert response.body == b"# Synthetic internal report"
    assert_lifecycle(
        events,
        "underwriting_report_markdown_export",
        "APP-GENAI-003",
        "completed",
    )


def test_markdown_export_logs_failure(monkeypatch):
    events = setup_test(monkeypatch, genai_routes)

    def fail_export(report):
        raise RuntimeError("Synthetic Markdown export failure")

    monkeypatch.setattr(
        genai_routes.underwriting_report_service,
        "to_markdown",
        fail_export,
    )

    with pytest.raises(
        RuntimeError,
        match="Synthetic Markdown export failure",
    ):
        genai_routes.export_underwriting_report_markdown(
            report=SimpleNamespace(application_id="APP-GENAI-004"),
            request=make_request(),
        )

    assert_lifecycle(
        events,
        "underwriting_report_markdown_export",
        "APP-GENAI-004",
        "failed",
    )
    assert events[-1]["error_code"] == (
        "UNDERWRITING_REPORT_MARKDOWN_EXPORT_FAILED"
    )


def test_additional_information_draft_logs_success(monkeypatch):
    events = setup_test(monkeypatch, comm_routes)

    monkeypatch.setattr(
        comm_routes.customer_communication_service,
        "generate_additional_information_request",
        lambda payload: SimpleNamespace(
            status="DRAFT_REQUIRES_HUMAN_REVIEW"
        ),
    )

    comm_routes.create_additional_information_request(
        payload=SimpleNamespace(
            application_id="APP-COMM-001",
            customer_id="CUST-COMM-001",
        ),
        request=make_request(),
    )

    assert_lifecycle(
        events,
        "additional_information_request_draft",
        "APP-COMM-001",
        "completed",
    )


def test_additional_information_draft_logs_failure(monkeypatch):
    events = setup_test(monkeypatch, comm_routes)

    def fail_generation(payload):
        raise ValueError("Synthetic draft validation failure")

    monkeypatch.setattr(
        comm_routes.customer_communication_service,
        "generate_additional_information_request",
        fail_generation,
    )

    with pytest.raises(HTTPException) as exc_info:
        comm_routes.create_additional_information_request(
            payload=SimpleNamespace(
                application_id="APP-COMM-002",
                customer_id="CUST-COMM-002",
            ),
            request=make_request(),
        )

    assert exc_info.value.status_code == 422
    assert_lifecycle(
        events,
        "additional_information_request_draft",
        "APP-COMM-002",
        "failed",
    )
    assert events[-1]["error_code"] == (
        "ADDITIONAL_INFORMATION_DRAFT_REJECTED"
    )


def test_decision_communication_draft_logs_success(monkeypatch):
    events = setup_test(monkeypatch, comm_routes)

    monkeypatch.setattr(
        comm_routes.customer_communication_service,
        "generate_decision_communication",
        lambda payload: SimpleNamespace(
            status="DRAFT_REQUIRES_HUMAN_REVIEW"
        ),
    )

    comm_routes.create_decision_communication_draft(
        payload=SimpleNamespace(
            underwriting=SimpleNamespace(
                application_id="APP-COMM-003"
            ),
            communication_type="APPROVAL_COMMUNICATION",
        ),
        request=make_request(),
    )

    assert_lifecycle(
        events,
        "decision_communication_draft",
        "APP-COMM-003",
        "completed",
    )


def test_decision_communication_draft_logs_failure(monkeypatch):
    events = setup_test(monkeypatch, comm_routes)

    def fail_generation(payload):
        raise ValueError("Synthetic decision draft failure")

    monkeypatch.setattr(
        comm_routes.customer_communication_service,
        "generate_decision_communication",
        fail_generation,
    )

    with pytest.raises(HTTPException) as exc_info:
        comm_routes.create_decision_communication_draft(
            payload=SimpleNamespace(
                underwriting=SimpleNamespace(
                    application_id="APP-COMM-004"
                ),
                communication_type="REJECTION_COMMUNICATION",
            ),
            request=make_request(),
        )

    assert exc_info.value.status_code == 422
    assert_lifecycle(
        events,
        "decision_communication_draft",
        "APP-COMM-004",
        "failed",
    )
    assert events[-1]["error_code"] == (
        "DECISION_COMMUNICATION_DRAFT_REJECTED"
    )