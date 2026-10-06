from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models.credit_decision import CreditDecision
from backend.app.models.loan_application import LoanApplication


client = TestClient(app)


def unique(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10].upper()}"


def find_value(payload, *keys):
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


def seed_approved_credit_decision(
    application_id: str,
):
    """
    Controlled fixture for the downstream post-approval E2E path.

    The current governed policy may legitimately return REFER because
    Geography and Vintage/Repayment parameters are not configured.
    This fixture therefore does not modify policy behavior; it establishes
    the persisted approval prerequisite required by downstream services.
    """

    db = SessionLocal()

    try:
        application = db.get(
            LoanApplication,
            application_id,
        )

        assert application is not None

        application.status = "APPROVED"

        decision = CreditDecision(
            decision_id=unique("E2E-DEC"),
            application_id=application_id,
            credit_score=780,
            risk_grade="A",
            probability_of_default=Decimal("0.016572"),
            affordability_score=Decimal("90"),
            repayment_propensity=Decimal("80"),
            fraud_score=Decimal("5"),
            income_stability_score=Decimal("80"),
            recommended_amount=Decimal("150000"),
            recommended_tenure=12,
            recommended_emi=Decimal("13752.00"),
            foir=Decimal("39.59"),
            risk_segment="LOW_RISK",
            decision="APPROVE",
            confidence=Decimal("0.90"),
            reason_codes="E2E_POST_APPROVAL_FIXTURE",
            model_version="E2E-FIXTURE-01",
            policy_version="POL-2026.09",
            effective_from="2026-09-01",
            effective_to=None,
        )

        db.add(decision)
        db.commit()

    finally:
        db.close()


def test_end_to_end_post_approval_servicing():
    # ============================================================
    # 1. Unique identifiers
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

    assert_success(
        customer_response,
        "Customer creation",
    )

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

    assert_success(
        application_response,
        "Application creation",
    )

    # ============================================================
    # 4. Controlled APPROVE fixture
    # ============================================================

    seed_approved_credit_decision(
        application_id,
    )

    # ============================================================
    # 5. Sanction
    # ============================================================

    sanction_response = client.post(
        "/sanctions",
        json={
            "application_id": application_id,
            "sanctioned_amount": 150000,
            "sanctioned_tenure": 12,
            "sanctioned_emi": 13752.00,
            "interest_rate": 18,
            "approval_authority": "E2E_TEST",
            "terms_and_conditions": "E2E post-approval test",
            "expires_at": None,
        },
    )

    assert_success(
        sanction_response,
        "Sanction creation",
    )

    sanction_payload = sanction_response.json()

    sanction_id = find_value(
        sanction_payload,
        "sanction_id",
    )

    assert sanction_id

    # ============================================================
    # 6. Agreement
    # ============================================================

    agreement_response = client.post(
        "/agreements",
        json={
            "application_id": application_id,
            "sanction_id": sanction_id,
            "agreement_reference": unique("AGR"),
            "document_reference": unique("DOC"),
            "esign_provider": "E2E_TEST",
        },
    )

    assert_success(
        agreement_response,
        "Agreement creation",
    )

    agreement_payload = agreement_response.json()["data"]

    agreement_id = find_value(
        agreement_payload,
        "agreement_id",
    )

    assert agreement_id

    # ============================================================
    # 7. Agreement eSign initiation
    # ============================================================

    esign_reference = unique("ESIGN")

    esign_init_response = client.post(
        f"/agreements/{agreement_id}/sign",
        json={
            "esign_status": "INITIATED",
            "esign_reference": esign_reference,
            "failure_reason": None,
            "signed_at": None,
        },
    )

    assert_success(
        esign_init_response,
        "Agreement eSign initiation",
    )

    esign_init_payload = esign_init_response.json()["data"]

    assert esign_init_payload["esign_status"] == "INITIATED"
    assert esign_init_payload["agreement_status"] == "ACTIVE"

    # ============================================================
    # 8. Agreement eSign completion
    # ============================================================

    esign_complete_response = client.post(
        f"/agreements/{agreement_id}/sign",
        json={
            "esign_status": "SIGNED",
            "esign_reference": esign_reference,
            "failure_reason": None,
            "signed_at": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )

    assert_success(
        esign_complete_response,
        "Agreement eSign completion",
    )

    esign_complete_payload = esign_complete_response.json()["data"]

    assert esign_complete_payload["esign_status"] == "SIGNED"
    assert esign_complete_payload["agreement_status"] == "COMPLETED"


    # ============================================================
    # 9. Mandate
    # ============================================================

    mandate_response = client.post(
        "/mandates",
        json={
            "application_id": application_id,
            "mandate_reference": unique("MANDATE"),
            "mandate_type": "NACH",
            "provider": "E2E_TEST",
        },
    )

    assert_success(
        mandate_response,
        "Mandate creation",
    )

    mandate_payload = mandate_response.json()

    mandate_id = find_value(
        mandate_payload,
        "mandate_id",
    )

    assert mandate_id

    # ============================================================
    # 10. Mandate initiation
    # ============================================================

    mandate_init_response = client.post(
        f"/mandates/{mandate_id}/status",
        json={
            "status": "INITIATED",
            "failure_reason": None,
            "completed_at": None,
        },
    )

    assert_success(
        mandate_init_response,
        "Mandate initiation",
    )

    mandate_init_payload = mandate_init_response.json()["data"]

    assert mandate_init_payload["status"] == "INITIATED"

    # ============================================================
    # 11. Mandate completion
    # ============================================================

    mandate_complete_response = client.post(
        f"/mandates/{mandate_id}/status",
        json={
            "status": "COMPLETED",
            "failure_reason": None,
            "completed_at": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )

    assert_success(
        mandate_complete_response,
        "Mandate completion",
    )

    mandate_complete_payload = mandate_complete_response.json()["data"]

    assert mandate_complete_payload["status"] == "COMPLETED"

    # ============================================================
    # 12. Beneficiary
    # ============================================================

    beneficiary_response = client.post(
        "/disbursements/beneficiaries",
        json={
            "application_id": application_id,
            "account_holder_name": "E2E Test Customer",
            "account_number_reference": unique("ACCOUNT"),
            "ifsc_code": "HDFC0001234",
            "bank_name": "E2E Test Bank",
        },
    )

    assert_success(
        beneficiary_response,
        "Beneficiary creation",
    )

    beneficiary_payload = beneficiary_response.json()

    beneficiary_id = find_value(
        beneficiary_payload,
        "beneficiary_id",
    )

    assert beneficiary_id

    # ============================================================
    # 13. Beneficiary validation
    # ============================================================

    beneficiary_validation_response = client.post(
        f"/disbursements/beneficiaries/"
        f"{beneficiary_id}/validate"
    )

    assert_success(
        beneficiary_validation_response,
        "Beneficiary validation",
    )

    # ============================================================
    # 14. Disbursement eligibility
    # ============================================================

    eligibility_response = client.post(
        "/disbursements/eligibility",
        json={
            "application_id": application_id,
            "sanction_id": sanction_id,
            "disbursement_amount": 150000,
            "beneficiary_reference": beneficiary_id,
        },
    )

    assert_success(
        eligibility_response,
        "Disbursement eligibility",
    )

    eligibility_payload = eligibility_response.json()

    eligibility_value = find_value(
        eligibility_payload,
        "eligible",
        "is_eligible",
    )

    if eligibility_value is not None:
        assert eligibility_value is True, (
            f"Disbursement not eligible: {eligibility_payload}"
        )

    # ============================================================
    # 15. Create disbursement
    # ============================================================

    idempotency_key = unique("IDEMP")

    disbursement_response = client.post(
        "/disbursements",
        json={
            "application_id": application_id,
            "disbursement_amount": 150000,
            "sanction_id": sanction_id,
            "beneficiary_reference": beneficiary_id,
            "payment_provider": "E2E_TEST_BANK",
            "idempotency_key": idempotency_key,
        },
    )

    assert_success(
        disbursement_response,
        "Disbursement creation",
    )

    disbursement_payload = disbursement_response.json()

    disbursement_id = find_value(
        disbursement_payload,
        "disbursement_id",
    )

    assert disbursement_id

    # ============================================================
    # 13. CREATED -> INITIATED
    # ============================================================

    initiated_response = client.post(
        f"/disbursements/{disbursement_id}/status",
        json={
            "status": "INITIATED",
            "bank_reference": None,
            "failure_reason": None,
            "processed_at": None,
        },
    )

    assert_success(
        initiated_response,
        "Disbursement INITIATED",
    )

    # ============================================================
    # 14. INITIATED -> PROCESSING
    # ============================================================

    processing_response = client.post(
        f"/disbursements/{disbursement_id}/status",
        json={
            "status": "PROCESSING",
            "bank_reference": None,
            "failure_reason": None,
            "processed_at": None,
        },
    )

    assert_success(
        processing_response,
        "Disbursement PROCESSING",
    )

    processing_payload = processing_response.json()["data"]

    bank_reference = find_value(
        processing_payload,
        "bank_reference",
    )

    assert bank_reference, (
        "PROCESSING response did not provide the bank reference: "
        f"{processing_payload}"
    )

    # ============================================================
    # 15. Bank success webhook
    # ============================================================

    webhook_response = client.post(
        "/disbursements/webhooks/bank",
        json={
            "disbursement_id": disbursement_id,
            "bank_reference": bank_reference,
            "status": "SUCCESS",
            "bank_amount": 150000,
            "failure_reason": None,
        },
    )

    assert_success(
        webhook_response,
        "Bank success webhook",
    )

    # ============================================================
    # 16. Verify disbursement PROCESSED
    # ============================================================

    disbursement_get_response = client.get(
        f"/disbursements/{disbursement_id}"
    )

    assert_success(
        disbursement_get_response,
        "Disbursement retrieval",
    )

    final_disbursement = disbursement_get_response.json()["data"]

    final_status = find_value(
        final_disbursement,
        "status",
    )

    assert final_status == "PROCESSED"

    # ============================================================
    # 17. Repayment schedule
    # ============================================================

    first_due_date = (
        datetime.now(timezone.utc)
    )

    schedule_response = client.post(
        "/repayments/schedule",
        json={
            "application_id": application_id,
            "disbursement_id": disbursement_id,
            "principal": 150000,
            "annual_interest_rate": 18,
            "tenure_months": 12,
            "first_due_date": first_due_date.isoformat(),
        },
    )

    assert_success(
        schedule_response,
        "Repayment schedule generation",
    )

    schedule_payload = schedule_response.json()["data"]

    assert isinstance(schedule_payload, list)
    assert len(schedule_payload) == 12

    first_installment = schedule_payload[0]
    second_installment = schedule_payload[1]

    first_schedule_id = find_value(
        first_installment,
        "repayment_schedule_id",
        "schedule_id",
    )

    second_schedule_id = find_value(
        second_installment,
        "repayment_schedule_id",
        "schedule_id",
    )

    assert first_schedule_id
    assert second_schedule_id

    first_amount = first_installment["total_due"]
    second_amount = second_installment["total_due"]

    assert first_amount is not None
    assert second_amount is not None

    assert Decimal(first_amount) > 0
    assert Decimal(second_amount) > 0

    # ============================================================
    # 18. Standalone repayment - installment 1
    # ============================================================

    repayment_response = client.post(
        "/repayments/record",
        json={
            "application_id": application_id,
            "repayment_schedule_id": first_schedule_id,
            "repayment_amount": first_amount,
            "repayment_reference": unique("REPAY"),
            "payment_mode": "NACH",
            "payment_provider": "E2E_TEST_BANK",
        },
    )

    assert_success(
        repayment_response,
        "Repayment recording",
    )

    repayment_payload = repayment_response.json()

    assert repayment_payload is not None

    # ============================================================
    # 19. Collection + repayment atomic workflow
    #     Uses installment 2 so we do not double-record installment 1.
    # ============================================================

    collection_response = client.post(
        "/collections/record",
        json={
            "application_id": application_id,
            "repayment_schedule_id": second_schedule_id,
            "repayment_amount": second_amount,
            "collection_reference": unique("COLL"),
            "collection_channel": "DIGITAL",
            "payment_mode": "NACH",
            "payment_provider": "E2E_TEST_BANK",
            "remarks": "E2E post-approval servicing test",
        },
    )

    assert_success(
        collection_response,
        "Collection recording",
    )

    collection_payload = collection_response.json()["data"]

    assert collection_payload is not None

    # ============================================================
    # 20. Reconciliation
    # ============================================================

    reconciliation_response = client.post(
        "/post-disbursement/reconciliation/check",
        params={
            "disbursement_id": disbursement_id,
            "bank_reference": bank_reference,
            "bank_amount": 150000,
        },
    )

    assert_success(
        reconciliation_response,
        "Disbursement reconciliation",
    )