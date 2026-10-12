from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.app.api.routes import agreements as agreement_routes
from backend.app.api.routes import mandates as mandate_routes


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
    request.state.request_id = "REQ-AGREEMENT-MANDATE-TEST"
    return request


class FakeDB:
    def __init__(self, entity):
        self.entity = entity

    def get(self, model, entity_id):
        return self.entity
    
    def rollback(self):
        pass


def setup_logging(monkeypatch, *route_modules):
    events = []

    for module in route_modules:
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


def test_agreement_creation_logs_success(monkeypatch):
    events = setup_logging(monkeypatch, agreement_routes)

    agreement = SimpleNamespace(
        application_id="APP-AGR-LOG-001",
        sanction_id="SAN-AGR-LOG-001",
        agreement_reference="TEST-AGR-REF",
        document_reference="TEST-DOC-REF",
        esign_provider="MOCK",
    )

    monkeypatch.setattr(
        agreement_routes.agreement_service,
        "create_agreement",
        lambda **kwargs: agreement,
    )
    monkeypatch.setattr(
        agreement_routes,
        "AgreementResponse",
        SimpleNamespace(model_validate=lambda value: value),
    )

    agreement_routes.create_agreement(
        agreement=agreement,
        request=make_request(),
        db=None,
    )

    assert [event["event"] for event in events] == [
        "started",
        "completed",
    ]
    assert all(
        event["workflow"] == "agreement_creation"
        for event in events
    )


@pytest.mark.parametrize(
    ("esign_status", "expected_workflow"),
    [
        ("INITIATED", "agreement_esign_initiation"),
        ("COMPLETED", "agreement_esign_completion"),
    ],
)
def test_agreement_esign_logs_success(
    monkeypatch,
    esign_status,
    expected_workflow,
):
    events = setup_logging(monkeypatch, agreement_routes)

    agreement = SimpleNamespace(
        application_id="APP-ESIGN-LOG-001",
        esign_provider="MOCK",
    )

    monkeypatch.setattr(
        agreement_routes,
        "AgreementResponse",
        SimpleNamespace(model_validate=lambda value: value),
    )

    if esign_status == "INITIATED":
        monkeypatch.setattr(
            agreement_routes.agreement_service,
            "initiate_esign",
            lambda **kwargs: agreement,
        )
    else:
        monkeypatch.setattr(
            agreement_routes.agreement_service,
            "complete_esign",
            lambda **kwargs: agreement,
        )

    sign_request = SimpleNamespace(
        esign_status=esign_status,
        esign_reference="TEST-ESIGN-REF",
        signed_at=None,
        failure_reason=None,
    )

    agreement_routes.update_agreement_sign(
        agreement_id="AGR-APP-ESIGN-LOG-001",
        sign_request=sign_request,
        request=make_request(),
        db=FakeDB(agreement),
    )

    assert [event["event"] for event in events] == [
        "started",
        "completed",
    ]
    assert all(
        event["workflow"] == expected_workflow
        for event in events
    )


def test_mandate_creation_logs_success(monkeypatch):
    events = setup_logging(monkeypatch, mandate_routes)

    mandate = SimpleNamespace(
        application_id="APP-MANDATE-LOG-001",
        mandate_reference="TEST-MANDATE-REF",
        mandate_type="NACH",
        provider="MOCK",
    )

    monkeypatch.setattr(
        mandate_routes.mandate_service,
        "create_mandate",
        lambda **kwargs: mandate,
    )
    monkeypatch.setattr(
        mandate_routes,
        "MandateResponse",
        SimpleNamespace(model_validate=lambda value: value),
    )

    mandate_routes.create_mandate(
        mandate=mandate,
        request=make_request(),
        db=None,
    )

    assert [event["event"] for event in events] == [
        "started",
        "completed",
    ]
    assert all(
        event["workflow"] == "mandate_creation"
        for event in events
    )


def test_mandate_initiation_logs_success(monkeypatch):
    events = setup_logging(monkeypatch, mandate_routes)

    mandate = SimpleNamespace(
        application_id="APP-MANDATE-LOG-002",
    )

    monkeypatch.setattr(
        mandate_routes.mandate_service,
        "initiate_mandate",
        lambda **kwargs: mandate,
    )
    monkeypatch.setattr(
        mandate_routes,
        "MandateResponse",
        SimpleNamespace(model_validate=lambda value: value),
    )

    mandate_routes.update_mandate_status(
        mandate_id="MANDATE-APP-MANDATE-LOG-002",
        update=SimpleNamespace(
            status="INITIATED",
            failure_reason=None,
            completed_at=None,
        ),
        request=make_request(),
        db=FakeDB(mandate),
    )

    assert [event["event"] for event in events] == [
        "started",
        "completed",
    ]
    assert all(
        event["workflow"] == "mandate_initiation"
        for event in events
    )


def test_mandate_initiation_logs_failure(monkeypatch):
    events = setup_logging(monkeypatch, mandate_routes)

    mandate = SimpleNamespace(
        application_id="APP-MANDATE-LOG-003",
    )

    def fail_initiation(**kwargs):
        raise ValueError("SYNTHETIC_MANDATE_ERROR")

    monkeypatch.setattr(
        mandate_routes.mandate_service,
        "initiate_mandate",
        fail_initiation,
    )

    with pytest.raises(HTTPException) as exc_info:
        mandate_routes.update_mandate_status(
            mandate_id="MANDATE-APP-MANDATE-LOG-003",
            update=SimpleNamespace(
                status="INITIATED",
                failure_reason=None,
                completed_at=None,
            ),
            request=make_request(),
            db=FakeDB(mandate),
        )

    assert exc_info.value.status_code == 400
    assert [event["event"] for event in events] == [
        "started",
        "failed",
    ]
    assert events[-1]["error_code"] == (
        "MANDATE_STATUS_UPDATE_FAILED"
    )