from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


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


def test_end_to_end_origination_to_manual_review():
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
            "report_reference": unique("BUREAU"),
        },
    )

    assert_success(
        bureau_response,
        "Bureau report ingestion",
    )

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
        f"/borrower-360/{customer_id}",
        params={
            "application_id": application_id,
        },
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

    assert manual_review_payload is not None

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

    assert exception_payload is not None