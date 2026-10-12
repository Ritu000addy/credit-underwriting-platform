from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.app.api.routes import applications
from backend.app.api.routes import customers
from backend.app.api.routes import documents
from backend.app.api.routes import bureau
from backend.app.api.routes import bank_analysis
from backend.app.api.routes import employment
from backend.app.api.routes import device_behaviour
from backend.app.api.routes import internal_history


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
    request.state.request_id = "REQ-ORIGINATION-LOG-TEST"
    return request


def build_cases():
    return [
        {
            "name": "application",
            "module": applications,
            "route": "create_application",
            "service": "application_service",
            "service_method": "create_application",
            "body_arg": "application",
            "body": SimpleNamespace(
                application_id="APP-LOG-001",
            ),
            "result": SimpleNamespace(
                application_id="APP-LOG-001",
                status="RECEIVED",
            ),
            "response_schema": "ApplicationResponse",
            "workflow": "application_creation",
            "entity_type": "loan_application",
            "entity_id": "APP-LOG-001",
            "failure_type": ValueError,
            "failure_status": 409,
            "failure_code": "APPLICATION_CREATION_REJECTED",
        },
        {
            "name": "customer",
            "module": customers,
            "route": "create_customer",
            "service": "customer_service",
            "service_method": "create_customer",
            "body_arg": "customer",
            "body": SimpleNamespace(
                customer_id="CUST-LOG-001",
                kyc_status="PENDING",
                pan=None,
                aadhaar_reference=None,
                aadhaar_kyc_status=None,
                dob=None,
                address=None,
            ),
            "result": SimpleNamespace(
                customer_id="CUST-LOG-001",
            ),
            "response_schema": "CustomerResponse",
            "workflow": "customer_creation",
            "entity_type": "customer",
            "entity_id": "CUST-LOG-001",
            "failure_type": ValueError,
            "failure_status": 409,
            "failure_code": "CUSTOMER_CREATION_REJECTED",
        },
        {
            "name": "document",
            "module": documents,
            "route": "create_document",
            "service": "document_service",
            "service_method": "create_document",
            "body_arg": "document",
            "body": SimpleNamespace(
                application_id="APP-LOG-003",
            ),
            "result": SimpleNamespace(
                application_id="APP-LOG-003",
            ),
            "response_schema": "DocumentResponse",
            "workflow": "document_creation",
            "entity_type": "document_ingestion",
            "entity_id": "APP-LOG-003",
            "failure_type": RuntimeError,
            "failure_status": None,
            "failure_code": "DOCUMENT_CREATION_FAILED",
        },
        {
            "name": "bureau",
            "module": bureau,
            "route": "create_bureau_report",
            "service": "bureau_report_service",
            "service_method": "create_report",
            "body_arg": "report",
            "body": SimpleNamespace(
                application_id="APP-LOG-004",
            ),
            "result": SimpleNamespace(
                application_id="APP-LOG-004",
            ),
            "response_schema": "BureauReportResponse",
            "workflow": "bureau_report_creation",
            "entity_type": "bureau_report",
            "entity_id": "APP-LOG-004",
            "failure_type": ValueError,
            "failure_status": 404,
            "failure_code": "BUREAU_REPORT_CREATION_REJECTED",
        },
        {
            "name": "bank_analysis",
            "module": bank_analysis,
            "route": "create_bank_analysis",
            "service": "bank_analysis_service",
            "service_method": "create_analysis",
            "body_arg": "analysis",
            "body": SimpleNamespace(
                application_id="APP-LOG-005",
            ),
            "result": SimpleNamespace(
                application_id="APP-LOG-005",
            ),
            "response_schema": "BankAnalysisResponse",
            "workflow": "bank_analysis_creation",
            "entity_type": "bank_analysis",
            "entity_id": "APP-LOG-005",
            "failure_type": ValueError,
            "failure_status": 404,
            "failure_code": "BANK_ANALYSIS_CREATION_REJECTED",
        },
        {
            "name": "employment",
            "module": employment,
            "route": "create_employment",
            "service": "employment_service",
            "service_method": "create_employment",
            "body_arg": "employment",
            "body": SimpleNamespace(
                application_id="APP-LOG-006",
            ),
            "result": SimpleNamespace(
                application_id="APP-LOG-006",
            ),
            "response_schema": "EmploymentResponse",
            "workflow": "employment_creation",
            "entity_type": "employment_analysis",
            "entity_id": "APP-LOG-006",
            "failure_type": RuntimeError,
            "failure_status": None,
            "failure_code": "EMPLOYMENT_CREATION_FAILED",
        },
        {
            "name": "device_behaviour",
            "module": device_behaviour,
            "route": "create_device_behaviour",
            "service": "device_behaviour_service",
            "service_method": "create_device_behaviour",
            "body_arg": "device_behaviour",
            "body": SimpleNamespace(
                application_id="APP-LOG-007",
            ),
            "result": SimpleNamespace(
                application_id="APP-LOG-007",
            ),
            "response_schema": "DeviceBehaviourResponse",
            "workflow": "device_behaviour_creation",
            "entity_type": "device_behaviour_analysis",
            "entity_id": "APP-LOG-007",
            "failure_type": RuntimeError,
            "failure_status": None,
            "failure_code": "DEVICE_BEHAVIOUR_CREATION_FAILED",
        },
        {
            "name": "internal_history",
            "module": internal_history,
            "route": "create_internal_history",
            "service": "internal_history_service",
            "service_method": "create_internal_history",
            "body_arg": "history",
            "body": SimpleNamespace(
                application_id="APP-LOG-008",
            ),
            "result": SimpleNamespace(
                application_id="APP-LOG-008",
            ),
            "response_schema": "InternalHistoryResponse",
            "workflow": "internal_history_creation",
            "entity_type": "internal_loan_history",
            "entity_id": "APP-LOG-008",
            "failure_type": RuntimeError,
            "failure_status": None,
            "failure_code": "INTERNAL_HISTORY_CREATION_FAILED",
        },
    ]


def setup_test(monkeypatch, case):
    events = []
    module = case["module"]

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

    monkeypatch.setattr(
        module,
        case["response_schema"],
        SimpleNamespace(
            model_validate=lambda value, **kwargs: value
        ),
    )

    return events


def invoke_route(case):
    route = getattr(case["module"], case["route"])

    return route(
        **{
            case["body_arg"]: case["body"],
            "request": make_request(),
            "db": None,
        }
    )


@pytest.mark.parametrize(
    "case",
    build_cases(),
    ids=lambda case: case["name"],
)
def test_origination_success_logs_lifecycle(monkeypatch, case):
    events = setup_test(monkeypatch, case)

    service = getattr(case["module"], case["service"])

    monkeypatch.setattr(
        service,
        case["service_method"],
        lambda *args, **kwargs: case["result"],
    )

    invoke_route(case)

    assert [event["event"] for event in events] == [
        "started",
        "completed",
    ]

    assert all(
        event["workflow"] == case["workflow"]
        for event in events
    )

    assert all(
        event["entity_type"] == case["entity_type"]
        for event in events
    )

    assert all(
        event["entity_id"] == case["entity_id"]
        for event in events
    )


@pytest.mark.parametrize(
    "case",
    build_cases(),
    ids=lambda case: case["name"],
)
def test_origination_failure_logs_failed_event(monkeypatch, case):
    events = setup_test(monkeypatch, case)

    service = getattr(case["module"], case["service"])
    error_type = case["failure_type"]

    def fail_service(*args, **kwargs):
        raise error_type("Synthetic ingestion failure")

    monkeypatch.setattr(
        service,
        case["service_method"],
        fail_service,
    )

    if case["failure_status"] is not None:
        with pytest.raises(HTTPException) as exc_info:
            invoke_route(case)

        assert exc_info.value.status_code == case["failure_status"]
    else:
        with pytest.raises(
            RuntimeError,
            match="Synthetic ingestion failure",
        ):
            invoke_route(case)

    assert [event["event"] for event in events] == [
        "started",
        "failed",
    ]

    assert all(
        event["workflow"] == case["workflow"]
        for event in events
    )

    assert all(
        event["entity_id"] == case["entity_id"]
        for event in events
    )

    assert events[-1]["error_code"] == case["failure_code"]