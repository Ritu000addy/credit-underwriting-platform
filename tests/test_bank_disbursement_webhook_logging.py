from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.app.api.routes import disbursements as routes


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
    request.state.request_id = "REQ-BANK-WEBHOOK-TEST-001"
    return request


class FakeDB:
    def __init__(self, disbursement):
        self.disbursement = disbursement

    def get(self, model, entity_id):
        return self.disbursement


def setup_test(monkeypatch, status="INITIATED"):
    events = []

    disbursement = SimpleNamespace(
        disbursement_id="DISB-WEBHOOK-TEST-001",
        application_id="APP-WEBHOOK-TEST-001",
        status=status,
        bank_reference="BANK-REF-TEST-001",
        processed_at=None,
        failure_reason=None,
    )

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
    monkeypatch.setattr(
        routes.audit_log_service,
        "log",
        lambda **kwargs: None,
    )

    return events, disbursement


def make_webhook(status="SUCCESS", bank_reference="BANK-REF-TEST-001"):
    return SimpleNamespace(
        disbursement_id="DISB-WEBHOOK-TEST-001",
        status=status,
        bank_reference=bank_reference,
        bank_amount=Decimal("1000.00"),
        failure_reason=None,
    )


def test_successful_bank_webhook_logs_completion(monkeypatch):
    events, disbursement = setup_test(monkeypatch)

    def mark_processing(**kwargs):
        kwargs["disbursement"].status = "PROCESSING"
        return kwargs["disbursement"]

    def process_disbursement(**kwargs):
        item = kwargs["disbursement"]
        item.status = "PROCESSED"
        item.bank_reference = kwargs["bank_reference"]
        return item

    monkeypatch.setattr(
        routes.disbursement_service,
        "mark_processing",
        mark_processing,
    )
    monkeypatch.setattr(
        routes.disbursement_service,
        "process_disbursement",
        process_disbursement,
    )
    monkeypatch.setattr(
        routes.reconciliation_service,
        "reconcile_disbursement",
        lambda **kwargs: SimpleNamespace(
            status="MATCHED",
            bank_amount=Decimal("1000.00"),
            expected_amount=Decimal("1000.00"),
            mismatch_reason=None,
        ),
    )

    routes.bank_disbursement_webhook(
        webhook=make_webhook(),
        request=make_request(),
        db=FakeDB(disbursement),
    )

    assert [event["event"] for event in events] == [
        "started",
        "completed",
    ]
    assert events[-1]["workflow"] == "bank_disbursement_webhook"
    assert events[-1]["status"] == "PROCESSED"


def test_bank_reference_mismatch_logs_failure(monkeypatch):
    events, disbursement = setup_test(monkeypatch)

    with pytest.raises(HTTPException) as exc_info:
        routes.bank_disbursement_webhook(
            webhook=make_webhook(bank_reference="WRONG-REF"),
            request=make_request(),
            db=FakeDB(disbursement),
        )

    assert exc_info.value.status_code == 400
    assert events[0]["event"] == "started"
    assert events[-1]["event"] == "failed"
    assert events[-1]["error_code"] == "BANK_REFERENCE_MISMATCH"


def test_duplicate_success_webhook_logs_completion(monkeypatch):
    events, disbursement = setup_test(monkeypatch, status="PROCESSED")

    monkeypatch.setattr(
        routes.reconciliation_service,
        "reconcile_disbursement",
        lambda **kwargs: SimpleNamespace(
            status="MATCHED",
            bank_amount=Decimal("1000.00"),
            expected_amount=Decimal("1000.00"),
            mismatch_reason=None,
        ),
    )

    routes.bank_disbursement_webhook(
        webhook=make_webhook(),
        request=make_request(),
        db=FakeDB(disbursement),
    )

    assert [event["event"] for event in events] == [
        "started",
        "completed",
    ]
    assert events[-1]["status"] == "PROCESSED"


def test_duplicate_failed_webhook_logs_completion(monkeypatch):
    events, disbursement = setup_test(monkeypatch, status="FAILED")

    routes.bank_disbursement_webhook(
        webhook=make_webhook(status="FAILED"),
        request=make_request(),
        db=FakeDB(disbursement),
    )

    assert [event["event"] for event in events] == [
        "started",
        "completed",
    ]
    assert events[-1]["status"] == "FAILED"