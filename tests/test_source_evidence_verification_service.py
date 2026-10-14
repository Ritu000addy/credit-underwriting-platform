
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import backend.app.services.source_evidence_verification_service as verification_module
from backend.app.models.bank_analysis import BankAnalysis
from backend.app.models.bureau_report import BureauReport


class FakeQuery:
    def __init__(self, record):
        self.record = record

    def filter(self, *args, **kwargs):
        return self

    def with_for_update(self):
        return self

    def one_or_none(self):
        return self.record


class FakeSession:
    def __init__(self, record=None):
        self.record = record
        self.commit_count = 0
        self.rollback_count = 0
        self.refreshed_record = None

    def query(self, model):
        return FakeQuery(self.record)

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

    def refresh(self, record):
        self.refreshed_record = record


def make_record(status="UNVERIFIED"):
    return SimpleNamespace(
        application_id="APP-VERIFY-TEST-001",
        verification_status=status,
        verified_by=None,
        verified_at=None,
    )


@pytest.mark.parametrize(
    (
        "method_name",
        "model",
        "record_id",
        "expected_action",
        "expected_entity",
    ),
    [
        (
            "verify_bureau_report",
            BureauReport,
            "BUREAU-VERIFY-001",
            "BUREAU_REPORT_VERIFIED",
            "BUREAU_REPORT",
        ),
        (
            "verify_bank_analysis",
            BankAnalysis,
            "BANK-VERIFY-001",
            "BANK_ANALYSIS_VERIFIED",
            "BANK_ANALYSIS",
        ),
    ],
)
def test_verification_records_reviewer_and_audit(
    monkeypatch,
    method_name,
    model,
    record_id,
    expected_action,
    expected_entity,
):
    record = make_record()
    db = FakeSession(record)
    audit_calls = []

    def fake_audit_log(**kwargs):
        audit_calls.append(kwargs)

    monkeypatch.setattr(
        verification_module.audit_log_service,
        "log",
        fake_audit_log,
    )

    service = verification_module.source_evidence_verification_service
    method = getattr(service, method_name)

    result = method(
        db=db,
        **{
            "bureau_report_id"
            if model is BureauReport
            else "bank_analysis_id": record_id,
        },
        reviewer_id="reviewer.one",
    )

    assert result is record
    assert record.verification_status == "VERIFIED"
    assert record.verified_by == "reviewer.one"
    assert record.verified_at is not None

    assert db.commit_count == 1
    assert db.rollback_count == 0
    assert db.refreshed_record is record

    assert len(audit_calls) == 1
    assert audit_calls[0]["application_id"] == record.application_id
    assert audit_calls[0]["actor_type"] == "HUMAN_REVIEWER"
    assert audit_calls[0]["actor_reference"] == "reviewer.one"
    assert audit_calls[0]["action"] == expected_action
    assert audit_calls[0]["entity_type"] == expected_entity
    assert audit_calls[0]["entity_reference"] == record_id
    assert audit_calls[0]["previous_state"] == "UNVERIFIED"
    assert audit_calls[0]["new_state"] == "VERIFIED"


@pytest.mark.parametrize(
    ("method_name", "argument_name", "record_id"),
    [
        (
            "verify_bureau_report",
            "bureau_report_id",
            "BUREAU-MISSING",
        ),
        (
            "verify_bank_analysis",
            "bank_analysis_id",
            "BANK-MISSING",
        ),
    ],
)
def test_verification_rejects_missing_records(
    method_name,
    argument_name,
    record_id,
):
    db = FakeSession(record=None)
    service = verification_module.source_evidence_verification_service

    with pytest.raises(ValueError) as exc:
        getattr(service, method_name)(
            db=db,
            **{argument_name: record_id},
            reviewer_id="reviewer.one",
        )

    expected = (
        "BUREAU_REPORT_NOT_FOUND"
        if argument_name == "bureau_report_id"
        else "BANK_ANALYSIS_NOT_FOUND"
    )
    assert str(exc.value) == expected
    assert db.commit_count == 0
    assert db.rollback_count == 1


def test_verification_rejects_already_verified_record():
    db = FakeSession(make_record(status="VERIFIED"))
    service = verification_module.source_evidence_verification_service

    with pytest.raises(
        ValueError,
        match="SOURCE_EVIDENCE_NOT_ELIGIBLE_FOR_VERIFICATION",
    ):
        service.verify_bureau_report(
            db=db,
            bureau_report_id="BUREAU-ALREADY-VERIFIED",
            reviewer_id="reviewer.one",
        )

    assert db.commit_count == 0
    assert db.rollback_count == 1


@pytest.mark.parametrize(
    ("reviewer_id", "expected_error"),
    [
        ("", "REVIEWER_REQUIRED"),
        (None, "REVIEWER_REQUIRED"),
        ("?", "REVIEWER_ID_INVALID"),
    ],
)
def test_verification_rejects_invalid_reviewer(
    reviewer_id,
    expected_error,
):
    db = FakeSession(make_record())
    service = verification_module.source_evidence_verification_service

    with pytest.raises(ValueError, match=expected_error):
        service.verify_bank_analysis(
            db=db,
            bank_analysis_id="BANK-VERIFY-002",
            reviewer_id=reviewer_id,
        )

    assert db.commit_count == 0


def test_audit_failure_rolls_back_verification(monkeypatch):
    db = FakeSession(make_record())
    service = verification_module.source_evidence_verification_service

    monkeypatch.setattr(
        verification_module.audit_log_service,
        "log",
        Mock(side_effect=RuntimeError("simulated audit failure")),
    )

    with pytest.raises(RuntimeError, match="simulated audit failure"):
        service.verify_bureau_report(
            db=db,
            bureau_report_id="BUREAU-AUDIT-FAIL",
            reviewer_id="reviewer.one",
        )

    assert db.commit_count == 0
    assert db.rollback_count == 1