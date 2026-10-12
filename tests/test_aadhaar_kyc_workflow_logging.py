from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.app.api.routes import aadhaar_kyc as routes


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
    request.state.request_id = "REQ-AADHAAR-KYC-TEST"
    return request


class FakeDB:
    def __init__(self, customer=None, fail_commit=False):
        self.customer = customer
        self.fail_commit = fail_commit
        self.commits = 0
        self.rollbacks = 0

    def get(self, model, customer_id):
        return self.customer

    def commit(self):
        self.commits += 1
        if self.fail_commit:
            raise RuntimeError("Synthetic database commit failure")

    def rollback(self):
        self.rollbacks += 1

    def refresh(self, entity):
        pass


def setup_test(monkeypatch, customer_exists=True, fail_commit=False):
    events = []
    customer = (
        SimpleNamespace(
            aadhaar_reference=None,
            aadhaar_kyc_status=None,
        )
        if customer_exists
        else None
    )
    db = FakeDB(customer=customer, fail_commit=fail_commit)

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
        routes,
        "AadhaarKYCResponse",
        SimpleNamespace(model_validate=lambda value: value),
    )

    return events, db, customer


def assert_events(events, workflow, customer_id, final_event):
    assert [item["event"] for item in events] == [
        "started",
        final_event,
    ]
    assert all(item["workflow"] == workflow for item in events)
    assert all(item["entity_type"] == "customer_aadhaar_kyc" for item in events)
    assert all(item["entity_id"] == customer_id for item in events)


def assert_sensitive_values_not_logged(events):
    event_text = repr(events)

    assert "synthetic-aadhaar-number" not in event_text
    assert "synthetic-otp" not in event_text
    assert "synthetic-session-token" not in event_text
    assert "synthetic-session-id" not in event_text


def test_send_aadhaar_otp_logs_success(monkeypatch):
    events, db, _ = setup_test(monkeypatch)

    monkeypatch.setattr(
        routes.aadhaar_kyc_service,
        "send_otp",
        lambda **kwargs: SimpleNamespace(status="OTP_SENT"),
    )

    routes.send_aadhaar_otp(
        customer_id="CUST-KYC-001",
        aadhaar_number="synthetic-aadhaar-number",
        user_consent=True,
        request=make_request(),
        user_id="TEST-USER",
        workflow_session_token="synthetic-session-token",
        db=db,
    )

    assert_events(
        events, "aadhaar_otp_send", "CUST-KYC-001", "completed"
    )
    assert_sensitive_values_not_logged(events)


def test_send_aadhaar_otp_logs_validation_failure(monkeypatch):
    events, db, _ = setup_test(monkeypatch)

    def fail_send(**kwargs):
        raise ValueError("Synthetic OTP request rejection")

    monkeypatch.setattr(
        routes.aadhaar_kyc_service,
        "send_otp",
        fail_send,
    )

    with pytest.raises(HTTPException) as exc_info:
        routes.send_aadhaar_otp(
            customer_id="CUST-KYC-002",
            aadhaar_number="synthetic-aadhaar-number",
            user_consent=True,
            request=make_request(),
            workflow_session_token="synthetic-session-token",
            db=db,
        )

    assert exc_info.value.status_code == 400
    assert_events(
        events, "aadhaar_otp_send", "CUST-KYC-002", "failed"
    )
    assert events[-1]["error_code"] == "AADHAAR_OTP_REQUEST_REJECTED"
    assert_sensitive_values_not_logged(events)


def test_send_aadhaar_otp_logs_provider_failure(monkeypatch):
    events, db, _ = setup_test(monkeypatch)

    def fail_send(**kwargs):
        raise RuntimeError("Synthetic OTP provider failure")

    monkeypatch.setattr(
        routes.aadhaar_kyc_service,
        "send_otp",
        fail_send,
    )

    with pytest.raises(HTTPException) as exc_info:
        routes.send_aadhaar_otp(
            customer_id="CUST-KYC-003",
            aadhaar_number="synthetic-aadhaar-number",
            user_consent=True,
            request=make_request(),
            workflow_session_token="synthetic-session-token",
            db=db,
        )

    assert exc_info.value.status_code == 502
    assert_events(
        events, "aadhaar_otp_send", "CUST-KYC-003", "failed"
    )
    assert events[-1]["error_code"] == "AADHAAR_OTP_PROVIDER_FAILED"
    assert_sensitive_values_not_logged(events)


def test_send_aadhaar_otp_logs_missing_customer(monkeypatch):
    events, db, _ = setup_test(monkeypatch, customer_exists=False)

    def unexpected_provider_call(**kwargs):
        pytest.fail("OTP provider should not be called")

    monkeypatch.setattr(
        routes.aadhaar_kyc_service,
        "send_otp",
        unexpected_provider_call,
    )

    with pytest.raises(HTTPException) as exc_info:
        routes.send_aadhaar_otp(
            customer_id="CUST-KYC-MISSING",
            aadhaar_number="synthetic-aadhaar-number",
            user_consent=True,
            request=make_request(),
            db=db,
        )

    assert exc_info.value.status_code == 404
    assert_events(
        events,
        "aadhaar_otp_send",
        "CUST-KYC-MISSING",
        "failed",
    )
    assert events[-1]["error_code"] == "CUSTOMER_NOT_FOUND"


def test_verify_aadhaar_otp_logs_success_and_persists_kyc(monkeypatch):
    events, db, customer = setup_test(monkeypatch)

    monkeypatch.setattr(
        routes.aadhaar_kyc_service,
        "verify_otp",
        lambda **kwargs: SimpleNamespace(
            masked_aadhaar="XXXX-XXXX-1234",
            kyc_status="VERIFIED",
        ),
    )

    routes.verify_aadhaar_otp(
        customer_id="CUST-KYC-004",
        session_id="synthetic-session-id",
        otp="synthetic-otp",
        request=make_request(),
        workflow_session_token="synthetic-session-token",
        db=db,
    )

    assert_events(
        events,
        "aadhaar_otp_verification",
        "CUST-KYC-004",
        "completed",
    )
    assert customer.aadhaar_reference == "XXXX-XXXX-1234"
    assert customer.aadhaar_kyc_status == "VERIFIED"
    assert db.commits == 1
    assert db.rollbacks == 0
    assert_sensitive_values_not_logged(events)


def test_verify_aadhaar_otp_logs_validation_failure(monkeypatch):
    events, db, _ = setup_test(monkeypatch)

    def fail_verify(**kwargs):
        raise ValueError("Synthetic OTP verification rejection")

    monkeypatch.setattr(
        routes.aadhaar_kyc_service,
        "verify_otp",
        fail_verify,
    )

    with pytest.raises(HTTPException) as exc_info:
        routes.verify_aadhaar_otp(
            customer_id="CUST-KYC-005",
            session_id="synthetic-session-id",
            otp="synthetic-otp",
            request=make_request(),
            workflow_session_token="synthetic-session-token",
            db=db,
        )

    assert exc_info.value.status_code == 400
    assert_events(
        events,
        "aadhaar_otp_verification",
        "CUST-KYC-005",
        "failed",
    )
    assert events[-1]["error_code"] == (
        "AADHAAR_OTP_VERIFICATION_REJECTED"
    )
    assert_sensitive_values_not_logged(events)


def test_verify_aadhaar_otp_logs_provider_failure(monkeypatch):
    events, db, _ = setup_test(monkeypatch)

    def fail_verify(**kwargs):
        raise RuntimeError("Synthetic verification provider failure")

    monkeypatch.setattr(
        routes.aadhaar_kyc_service,
        "verify_otp",
        fail_verify,
    )

    with pytest.raises(HTTPException) as exc_info:
        routes.verify_aadhaar_otp(
            customer_id="CUST-KYC-006",
            session_id="synthetic-session-id",
            otp="synthetic-otp",
            request=make_request(),
            db=db,
        )

    assert exc_info.value.status_code == 502
    assert_events(
        events,
        "aadhaar_otp_verification",
        "CUST-KYC-006",
        "failed",
    )
    assert events[-1]["error_code"] == "AADHAAR_OTP_PROVIDER_FAILED"
    assert_sensitive_values_not_logged(events)


def test_verify_aadhaar_otp_logs_missing_customer(monkeypatch):
    events, db, _ = setup_test(monkeypatch, customer_exists=False)

    def unexpected_provider_call(**kwargs):
        pytest.fail("OTP provider should not be called")

    monkeypatch.setattr(
        routes.aadhaar_kyc_service,
        "verify_otp",
        unexpected_provider_call,
    )

    with pytest.raises(HTTPException) as exc_info:
        routes.verify_aadhaar_otp(
            customer_id="CUST-KYC-MISSING",
            session_id="synthetic-session-id",
            otp="synthetic-otp",
            request=make_request(),
            db=db,
        )

    assert exc_info.value.status_code == 404
    assert_events(
        events,
        "aadhaar_otp_verification",
        "CUST-KYC-MISSING",
        "failed",
    )
    assert events[-1]["error_code"] == "CUSTOMER_NOT_FOUND"


def test_verify_aadhaar_otp_logs_persistence_failure(monkeypatch):
    events, db, _ = setup_test(monkeypatch, fail_commit=True)

    monkeypatch.setattr(
        routes.aadhaar_kyc_service,
        "verify_otp",
        lambda **kwargs: SimpleNamespace(
            masked_aadhaar="XXXX-XXXX-1234",
            kyc_status="VERIFIED",
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="Synthetic database commit failure",
    ):
        routes.verify_aadhaar_otp(
            customer_id="CUST-KYC-007",
            session_id="synthetic-session-id",
            otp="synthetic-otp",
            request=make_request(),
            db=db,
        )

    assert_events(
        events,
        "aadhaar_otp_verification",
        "CUST-KYC-007",
        "failed",
    )
    assert events[-1]["error_code"] == "AADHAAR_KYC_PERSISTENCE_FAILED"
    assert db.commits == 1
    assert db.rollbacks == 1
    assert_sensitive_values_not_logged(events)