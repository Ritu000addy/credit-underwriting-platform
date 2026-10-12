from types import SimpleNamespace

import pytest
from starlette.requests import Request

from backend.app.api.routes import lms as routes


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
    request.state.request_id = "REQ-LMS-LOG-TEST"
    return request


def setup_test(monkeypatch):
    events = []

    monkeypatch.setattr(
        routes,
        "log_workflow_event",
        lambda **kwargs: events.append(kwargs),
    )
    monkeypatch.setattr(
        routes,
        "success_response",
        lambda **kwargs: kwargs,
    )

    for schema_name in (
        "LMSSanctionResponse",
        "LMSLoanStatusResponse",
        "LMSRepaymentScheduleResponse",
        "LMSServicingInstallmentResponse",
    ):
        monkeypatch.setattr(
            routes,
            schema_name,
            SimpleNamespace(model_validate=lambda value: value),
        )

    return events


def assert_success(events, workflow, entity_id):
    assert [event["event"] for event in events] == [
        "started",
        "completed",
    ]
    assert all(event["workflow"] == workflow for event in events)
    assert all(event["entity_id"] == entity_id for event in events)


def test_create_lms_loan_account_logs_success(monkeypatch):
    events = setup_test(monkeypatch)

    request_body = SimpleNamespace(
        sanction_id="SAN-LMS-001",
        application_id="APP-LMS-001",
    )
    result = SimpleNamespace(
        loan_account_id="LMS-LOAN-001",
        application_id="APP-LMS-001",
        sanction_id="SAN-LMS-001",
        loan_status="ACTIVE",
        created_at=None,
    )

    monkeypatch.setattr(
        routes.lms_service,
        "create_loan_account",
        lambda request: result,
    )

    routes.create_lms_loan_account(
        request=request_body,
        api_request=make_request(),
    )

    assert_success(
        events, "lms_loan_account_creation", "SAN-LMS-001"
    )
    assert events[-1]["status"] == "ACTIVE"


def test_update_lms_loan_status_logs_success(monkeypatch):
    events = setup_test(monkeypatch)

    request_body = SimpleNamespace(
        loan_account_id="LMS-LOAN-002",
        application_id="APP-LMS-002",
        loan_status="CLOSED",
    )
    result = SimpleNamespace(
        loan_account_id="LMS-LOAN-002",
        application_id="APP-LMS-002",
        loan_status="CLOSED",
        updated_at=None,
    )

    monkeypatch.setattr(
        routes.lms_service,
        "update_loan_status",
        lambda request: result,
    )

    routes.update_lms_loan_status(
        request=request_body,
        api_request=make_request(),
    )

    assert_success(
        events, "lms_loan_status_update", "LMS-LOAN-002"
    )
    assert events[-1]["status"] == "CLOSED"


def test_create_lms_repayment_schedule_logs_success(monkeypatch):
    events = setup_test(monkeypatch)

    request_body = SimpleNamespace(
        loan_account_id="LMS-LOAN-003",
        application_id="APP-LMS-003",
        sanction_id="SAN-LMS-003",
    )
    result = SimpleNamespace(
        repayment_schedule_id="SCHEDULE-003",
        loan_account_id="LMS-LOAN-003",
        application_id="APP-LMS-003",
        schedule_status="CREATED",
        created_at=None,
    )

    monkeypatch.setattr(
        routes.lms_service,
        "create_repayment_schedule",
        lambda request: result,
    )

    routes.create_lms_repayment_schedule(
        request=request_body,
        api_request=make_request(),
    )

    assert_success(
        events,
        "lms_repayment_schedule_creation",
        "LMS-LOAN-003:SAN-LMS-003",
    )
    assert events[-1]["status"] == "CREATED"


def test_create_lms_servicing_installment_logs_success(monkeypatch):
    events = setup_test(monkeypatch)

    request_body = SimpleNamespace(
        loan_account_id="LMS-LOAN-004",
        application_id="APP-LMS-004",
        repayment_schedule_id="SCHEDULE-004",
        installment_number=1,
    )
    result = SimpleNamespace(
        repayment_schedule_id="SCHEDULE-004",
        loan_account_id="LMS-LOAN-004",
        installment_number=1,
        schedule_status="CREATED",
    )

    monkeypatch.setattr(
        routes.lms_service,
        "create_servicing_installment",
        lambda request: result,
    )

    routes.create_lms_servicing_installment(
        request=request_body,
        api_request=make_request(),
    )

    assert_success(
        events,
        "lms_servicing_installment_creation",
        "SCHEDULE-004:1",
    )
    assert events[-1]["status"] == "CREATED"


@pytest.mark.parametrize(
    (
        "route_name",
        "service_method",
        "request_body",
        "workflow",
        "entity_id",
        "error_code",
    ),
    [
        (
            "create_lms_loan_account",
            "create_loan_account",
            SimpleNamespace(
                sanction_id="SAN-FAIL-001",
                application_id="APP-FAIL-001",
            ),
            "lms_loan_account_creation",
            "SAN-FAIL-001",
            "LMS_LOAN_ACCOUNT_CREATION_FAILED",
        ),
        (
            "update_lms_loan_status",
            "update_loan_status",
            SimpleNamespace(
                loan_account_id="LOAN-FAIL-002",
                application_id="APP-FAIL-002",
                loan_status="CLOSED",
            ),
            "lms_loan_status_update",
            "LOAN-FAIL-002",
            "LMS_LOAN_STATUS_UPDATE_FAILED",
        ),
        (
            "create_lms_repayment_schedule",
            "create_repayment_schedule",
            SimpleNamespace(
                loan_account_id="LOAN-FAIL-003",
                application_id="APP-FAIL-003",
                sanction_id="SAN-FAIL-003",
            ),
            "lms_repayment_schedule_creation",
            "LOAN-FAIL-003:SAN-FAIL-003",
            "LMS_REPAYMENT_SCHEDULE_CREATION_FAILED",
        ),
        (
            "create_lms_servicing_installment",
            "create_servicing_installment",
            SimpleNamespace(
                loan_account_id="LOAN-FAIL-004",
                application_id="APP-FAIL-004",
                repayment_schedule_id="SCHEDULE-FAIL-004",
                installment_number=1,
            ),
            "lms_servicing_installment_creation",
            "SCHEDULE-FAIL-004:1",
            "LMS_SERVICING_INSTALLMENT_CREATION_FAILED",
        ),
    ],
)
def test_lms_unexpected_failure_logs_failed_event(
    monkeypatch,
    route_name,
    service_method,
    request_body,
    workflow,
    entity_id,
    error_code,
):
    events = setup_test(monkeypatch)

    def fail_service(*args, **kwargs):
        raise RuntimeError("Synthetic LMS integration failure")

    monkeypatch.setattr(
        routes.lms_service,
        service_method,
        fail_service,
    )

    route = getattr(routes, route_name)

    with pytest.raises(
        RuntimeError,
        match="Synthetic LMS integration failure",
    ):
        route(
            request=request_body,
            api_request=make_request(),
        )

    assert [event["event"] for event in events] == [
        "started",
        "failed",
    ]
    assert all(event["workflow"] == workflow for event in events)
    assert all(event["entity_id"] == entity_id for event in events)
    assert events[-1]["error_code"] == error_code