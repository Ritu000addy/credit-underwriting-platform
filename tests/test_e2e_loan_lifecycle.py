from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app
from types import SimpleNamespace

import pytest

from backend.app.core.security import get_current_user

from backend.app.database import SessionLocal

from backend.app.models.bureau_report import BureauReport
from backend.app.models.bank_analysis import BankAnalysis
from backend.app.models.decision_trace import DecisionTrace
from backend.app.models.underwriting_feature_snapshot import (
    UnderwritingFeatureSnapshot,
)
from backend.app.models.credit_decision import CreditDecision

client = TestClient(app)


@pytest.fixture
def authenticated_credit_analyst():
    """Authenticate this test as a credit analyst without changing production auth."""
    previous_override = app.dependency_overrides.get(get_current_user)

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        user_id="E2E-TEST-ANALYST",
        username="e2e-test-analyst",
        role="CREDIT_ANALYST",
        is_active=True,
    )

    yield

    # Restore the previous override so other tests are unaffected.
    if previous_override is None:
        app.dependency_overrides.pop(get_current_user, None)
    else:
        app.dependency_overrides[get_current_user] = previous_override


def unique(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10].upper()}"


def find_value(payload, *keys):
    """
    Recursively find the first non-null value for one of the supplied keys.
    This keeps the E2E test independent of harmless response nesting.
    """
    if isinstance(payload, dict):
        for key in keys:
            if key in payload and payload[key] is not None:
                return payload[key]

        for value in payload.values():
            found = find_value(value, *keys)
            if found is not None:
                return found

    elif isinstance(payload, list):
        for item in payload:
            found = find_value(item, *keys)
            if found is not None:
                return found

    return None


def assert_success(response, step: str):
    assert response.status_code == 200, (
        f"{step} failed: "
        f"status={response.status_code}, "
        f"body={response.text}"
    )


def test_end_to_end_origination_to_manual_review(authenticated_credit_analyst,):
    # ============================================================
    # 1. Unique test identifiers
    # ============================================================

    customer_id = unique("E2E-CUST")
    application_id = unique("E2E-APP")

    # ============================================================
    # 2. Customer
    # ============================================================

    customer_response = client.post(
        "/customers",
        json={
            "customer_id": customer_id,
            "kyc_status": "VERIFIED",
            "pan": "ABCDE1234F",
            "aadhaar_reference": unique("AADHAAR"),
            "aadhaar_kyc_status": "VERIFIED",
            "dob": "1990-01-15",
            "address": "Pune, Maharashtra",
        },
    )

    assert_success(customer_response, "Customer creation")

    customer_payload = customer_response.json()

    returned_customer_id = find_value(
        customer_payload,
        "customer_id",
    )

    assert returned_customer_id == customer_id

    # ============================================================
    # 3. Application
    # ============================================================

    application_response = client.post(
        "/applications",
        json={
            "application_id": application_id,
            "customer_id": customer_id,
            "requested_amount": 150000,
            "loan_tenure_months": 12,
            "annual_interest_rate": 18,
        },
    )

    assert_success(application_response, "Application creation")


    # ============================================================
    # 3A. Source Data Ingestion
    # ============================================================

    bureau_reference = unique("BUREAU")

    bureau_response = client.post(
        "/bureau-reports",
        json={
            "application_id": application_id,
            "bureau_name": "E2E_BUREAU",
            "bureau_score": 780,
            "dpd": 0,
            "active_loans": 1,
            "total_outstanding": 10000,
            "write_offs": 0,
            "enquiries": 1,
            "report_reference": bureau_reference,
        },
    )

    assert_success(
        bureau_response,
        "Bureau report ingestion",
    )

    db = SessionLocal()
    try:
        bureau_report = (
            db.query(BureauReport)
            .filter(
                BureauReport.report_reference == bureau_reference,
                BureauReport.application_id == application_id,
            )
            .one()
        )

        bureau_report.verification_status = "VERIFIED"
        db.commit()
    finally:
        db.close()

    bank_response = client.post(
        "/bank-analysis",
        json={
            "application_id": application_id,
            "monthly_credits": 60000,
            "monthly_debits": 20000,
            "average_balance": 100000,
            "existing_emi": 10000,
            "bounce_count": 0,
            "transactions_count": 20,
            "income_trend": "STABLE",
            "analysis_reference": unique("BANK"),
        },
    )

    assert_success(
        bank_response,
        "Bank analysis ingestion",
    )

    db = SessionLocal()
    try:
        bank_analysis = (
            db.query(BankAnalysis)
            .filter(
                BankAnalysis.application_id == application_id
            )
            .one()
        )
        bank_analysis.verification_status = "VERIFIED"
        db.commit()
    finally:
        db.close()

    employment_response = client.post(
        "/employment",
        json={
            "application_id": application_id,
            "employment_type": "SALARIED",
            "employer_name": "E2E Test Employer",
            "monthly_income": 60000,
            "employment_vintage_months": 36,
            "business_name": None,
            "business_vintage_months": None,
            "gst_registered": None,
            "udyam_registered": None,
            "income_source": "SALARY",
            "analysis_reference": unique("EMP"),
        },
    )

    assert_success(
        employment_response,
        "Employment ingestion",
    )

    device_response = client.post(
        "/device-behaviour",
        json={
            "application_id": application_id,
            "device_id": unique("DEVICE"),
            "device_type": "MOBILE",
            "operating_system": "ANDROID",
            "app_version": "E2E-1.0",
            "ip_address": "192.168.1.10",
            "device_age_days": 180,
            "login_count": 10,
            "session_count": 12,
            "failed_login_count": 0,
            "application_velocity": 1,
            "device_velocity": 1,
            "ip_velocity": 1,
            "behavioural_risk_score": 5,
            "fraud_indicator": "CLEAR",
            "analysis_reference": unique("DEVICE-REF"),
        },
    )

    assert_success(
        device_response,
        "Device behaviour ingestion",
    )

    internal_history_response = client.post(
        "/internal-history",
        json={
            "application_id": application_id,
            "previous_loans_count": 1,
            "active_loans_count": 1,
            "closed_loans_count": 0,
            "total_previous_exposure": 50000,
            "total_outstanding_amount": 10000,
            "repayment_history": "GOOD",
            "dpd_count": 0,
            "max_dpd": 0,
            "overdue_amount": 0,
            "write_off_count": 0,
            "settlement_count": 0,
            "last_loan_date": "2025-12-15",
            "analysis_reference": unique("HISTORY"),
        },
    )

    assert_success(
        internal_history_response,
        "Internal history ingestion",
    )

    documents_response = client.post(
        "/documents",
        json={
            "application_id": application_id,
            "document_type": "BANK_STATEMENT",
            "document_name": "E2E Bank Statement",
            "document_category": "INCOME_PROOF",
            "document_reference": unique("DOC"),
            "document_source": "E2E_TEST",
            "verification_status": "VERIFIED",
            "verification_reference": unique("DOC-VERIFY"),
            "extracted_data": "Income verified for E2E test",
            "analysis_reference": unique("DOC-ANALYSIS"),
        },
    )

    assert_success(
        documents_response,
        "Document ingestion",
    )

    # ============================================================
    # 4. Borrower 360 aggregation
    # ============================================================

    borrower360_response = client.get(
        f"/borrower-360/{customer_id}/{application_id}",
    )

    assert_success(
        borrower360_response,
        "Borrower 360 aggregation",
    )

    borrower360_payload = borrower360_response.json()["data"]

    assert borrower360_payload["customer_id"] == customer_id
    assert borrower360_payload["kyc"] is not None
    assert borrower360_payload["credit_bureau"] is not None
    assert borrower360_payload["bank_cash_flow"] is not None
    assert borrower360_payload["employment_business"] is not None
    assert borrower360_payload["internal_history"] is not None
    assert borrower360_payload["device_behaviour"] is not None
    assert borrower360_payload["documents"] is not None


    # ============================================================
    # 5. Underwriting
    # ============================================================

    underwriting_response = client.post(
        "/underwriting/evaluate",
        json={
            "application": {
                "application_id": application_id,
                "customer_id": customer_id,
                "requested_amount": 150000,
                "loan_tenure_months": 12,
                "annual_interest_rate": 18,
            },
            "borrower": borrower360_payload,
        },
    )

    assert_success(
        underwriting_response,
        "Underwriting evaluation",
    )

    underwriting_payload = underwriting_response.json()["data"]

    decision_payload = underwriting_payload.get("decision")

    if isinstance(decision_payload, dict):
        decision = decision_payload.get(
            "decision",
            decision_payload.get("final_decision"),
        )
    else:
        decision = decision_payload

    assert decision in {
        "APPROVE",
        "REFER",
        "REJECT",
    }, (
        "Underwriting response did not contain a valid decision: "
        f"{underwriting_payload}"
    )

    assert decision == "REFER", (
        "Current governed policy is expected to REFER "
        "because Geography and Vintage/Repayment are "
        "not configured. "
        f"Actual decision={decision}; "
        f"response={underwriting_payload}"
    )

    decision_detail = underwriting_payload["decision"]

    assert "POLICY_DATA_INCOMPLETE" in (
        decision_detail.get("reason_codes") or []
    )

    assert underwriting_payload["policy"]["policy_status"] == "REFER"

        # Verify the persisted underwriting decision.
    persisted_response = client.get(
        f"/underwriting/{application_id}"
    )
    assert_success(
        persisted_response,
        "Persisted underwriting decision retrieval",
    )

    persisted_payload = persisted_response.json()["data"]

    assert persisted_payload["application_id"] == application_id
    assert persisted_payload["decision"] == decision
    assert "POLICY_DATA_INCOMPLETE" in (
        persisted_payload.get("reason_codes") or []
    )

    # Verify that decision-trace creation was audited.
    audit_response = client.get(
        f"/audit/{application_id}"
    )
    assert_success(audit_response, "Application audit retrieval")

    audit_payload = audit_response.json()["data"]
    audit_logs = audit_payload.get("audit_logs", [])

    assert any(
        entry.get("action") == "DECISION_TRACE_CREATED"
        and entry.get("entity_type") == "DECISION_TRACE"
        for entry in audit_logs
    ), "No decision-trace creation audit event was persisted"

        # Verify the persisted decision trace and its lineage.
    with SessionLocal() as db:
        traces = (
            db.query(DecisionTrace)
            .filter(
                DecisionTrace.application_id == application_id
            )
            .all()
        )

        assert len(traces) == 1, (
            f"Expected exactly one decision trace for {application_id}, "
            f"found {len(traces)}"
        )

        trace = traces[0]

        persisted_decision = db.get(
            CreditDecision,
            persisted_payload["decision_id"],
        )

        assert persisted_decision is not None, (
            "Persisted credit decision was not found"
        )
        assert persisted_decision.application_id == application_id
        assert persisted_decision.application_id == trace.application_id

        assert trace.decision_id == persisted_payload["decision_id"]
        assert trace.decision == persisted_payload["decision"]
        assert trace.policy_version == persisted_payload["policy_version"]
        assert "POLICY_DATA_INCOMPLETE" in (
            trace.reason_codes or []
        )

                # Verify policy evaluation was recorded consistently.
        assert trace.decision_metadata is not None
        assert (
            trace.decision_metadata.get("policy_evaluation_status")
            == "COMPLETED"
        )
        assert isinstance(trace.policy_evaluation, list)

            # Verify the feature snapshot is linked to the same decision.
        snapshot = (
            db.query(UnderwritingFeatureSnapshot)
            .filter(
                UnderwritingFeatureSnapshot.decision_id
                == persisted_payload["decision_id"]
            )
            .one_or_none()
        )

        assert snapshot is not None, (
            "No feature snapshot was persisted for the decision"
        )
        assert snapshot.application_id == application_id
        assert snapshot.decision_id == trace.decision_id
        assert trace.feature_snapshot_id == snapshot.feature_snapshot_id
        assert snapshot.features is not None
        assert isinstance(snapshot.features, dict)

        assert trace.model_version == persisted_payload["model_version"], (
            "Decision trace model version does not match the persisted decision"
        )

        assert snapshot.model_version == trace.model_version, (
            "Feature snapshot model version does not match the decision trace"
        )

        assert (
            snapshot.feature_version
            == trace.decision_metadata.get("feature_version")
        ), "Feature snapshot version does not match decision metadata"

    # ============================================================
    # 6. Manual Review created for REFER decision
    # ============================================================

    manual_review_response = client.get(
        f"/manual-review/{application_id}"
    )

    assert_success(
        manual_review_response,
        "Manual review retrieval",
    )

    manual_review_payload = manual_review_response.json()
    assert manual_review_payload["success"] is True

    manual_review = manual_review_payload["data"]

    assert manual_review is not None
    assert manual_review["application_id"] == application_id
    assert manual_review["review_id"]
    assert manual_review["review_status"] == "OPEN"
    assert manual_review["maker_checker_required"] is True
    assert manual_review["review_reason"]

    assert "POLICY_DATA_INCOMPLETE" in (
        manual_review["review_reason"]
    )


    # ============================================================
    # 7. Review Exception created for REFER
    # ============================================================

    exception_response = client.get(
        f"/review-exceptions/application/{application_id}"
    )

    assert_success(
        exception_response,
        "Review exception retrieval",
    )

    exception_payload = exception_response.json()
    assert exception_payload["success"] is True

    exceptions = exception_payload["data"]

    assert isinstance(exceptions, list)
    assert exceptions, "No review exception was created"

    matching_exceptions = [
        exception
        for exception in exceptions
        if exception["application_id"] == application_id
        and exception["exception_type"] == "UNDERWRITING_REFER"
    ]

    assert matching_exceptions, (
        "No UNDERWRITING_REFER exception exists "
        "for this application"
    )

    review_exception = matching_exceptions[0]

    assert (
        review_exception["review_id"]
        == manual_review["review_id"]
    )
    assert review_exception["status"] == "OPEN"
    assert review_exception["description"]
    assert "POLICY_DATA_INCOMPLETE" in (
        review_exception["description"]
    )
