from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.services.post_disbursement_service import (
    post_disbursement_service,
)

from tests.test_e2e_post_approval_servicing import (
    seed_approved_credit_decision,
)


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


def test_post_disbursement_flow():
    customer_id = unique("POST-CUST")
    application_id = unique("POST-APP")

    sanction_id = unique("POST-SANCTION")
    mandate_id = unique("POST-MANDATE")
    mandate_reference = unique("POST-MANDATE-REF")
    disbursement_id = unique("POST-DISBURSEMENT")
    repayment_schedule_id = unique("POST-REPAYMENT")

    # ============================================================
    # 1. Create fresh customer
    # ============================================================

    customer_response = client.post(
        "/customers",
        json={
            "customer_id": customer_id,
            "kyc_status": "VERIFIED",
            "pan": "ABCDR1234Z",
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
    # 2. Create fresh application
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
    # 3. Controlled APPROVE prerequisite
    # ============================================================

    seed_approved_credit_decision(
        application_id=application_id,
    )

    db = SessionLocal()

    try:
        # ============================================================
        # 4. Sanction
        # ============================================================

        sanction = post_disbursement_service.create_sanction(
            db=db,
            application_id=application_id,
            sanction_id=sanction_id,
            sanctioned_amount=Decimal("150000"),
            sanctioned_tenure=12,
            sanctioned_emi=Decimal("13327.32"),
            interest_rate=Decimal("12"),
            approval_authority="DEV-TEST",
            terms_and_conditions="Development test sanction",
        )

        assert sanction.sanction_id == sanction_id
        assert sanction.application_id == application_id
        assert sanction.sanctioned_amount == Decimal("150000")

        # ============================================================
        # 5. Agreement
        # ============================================================

        agreement_response = client.post(
            "/agreements",
            json={
                "application_id": application_id,
                "sanction_id": sanction_id,
                "agreement_reference": unique("POST-AGR"),
                "document_reference": unique("POST-DOC"),
                "esign_provider": "DEV-TEST",
            },
        )

        assert_success(
            agreement_response,
            "Agreement creation",
        )

        agreement_payload = agreement_response.json()
        agreement_id = agreement_payload["agreement_id"]

        assert agreement_id

        # ============================================================
        # 6. eSign initiation
        # ============================================================

        esign_reference = unique("POST-ESIGN")

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

        esign_init_payload = esign_init_response.json()

        assert esign_init_payload["esign_status"] == "INITIATED"
        assert esign_init_payload["agreement_status"] == "ACTIVE"

        # ============================================================
        # 7. eSign completion
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

        esign_complete_payload = (
            esign_complete_response.json()
        )

        assert (
            esign_complete_payload["esign_status"]
            == "SIGNED"
        )
        assert (
            esign_complete_payload["agreement_status"]
            == "COMPLETED"
        )

        # ============================================================
        # 8. Mandate
        # ============================================================

        mandate = post_disbursement_service.create_mandate(
            db=db,
            application_id=application_id,
            mandate_id=mandate_id,
            status="CREATED",
            mandate_reference=mandate_reference,
            mandate_type="NACH",
            provider="DEV-PROVIDER",
        )

        assert mandate.mandate_id == mandate_id
        assert mandate.application_id == application_id
        assert mandate.status == "CREATED"

        # ============================================================
        # 9. Mandate INITIATED
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
            "Mandate INITIATED",
        )

        mandate_init_payload = mandate_init_response.json()

        assert mandate_init_payload["status"] == "INITIATED"

        # ============================================================
        # 10. Mandate COMPLETED
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
            "Mandate COMPLETED",
        )

        mandate_complete_payload = (
            mandate_complete_response.json()
        )

        assert mandate_complete_payload["status"] == "COMPLETED"

        # ============================================================
        # 6. Disbursement
        # ============================================================

        disbursement = post_disbursement_service.create_disbursement(
            db=db,
            application_id=application_id,
            disbursement_id=disbursement_id,
            disbursement_amount=Decimal("150000"),
            sanction_id=sanction_id,
            beneficiary_reference="BENEFICIARY-REF-001",
            bank_reference="BANK-REF-001",
            payment_provider="DEV-PAYMENT-PROVIDER",
        )

        assert disbursement.disbursement_id == disbursement_id
        assert disbursement.application_id == application_id
        assert disbursement.sanction_id == sanction_id
        assert disbursement.disbursement_amount == Decimal("150000")
        assert disbursement.status == "CREATED"

        # ============================================================
        # 7. Repayment INITIATED
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

        initiated_payload = initiated_response.json()

        assert initiated_payload["status"] == "INITIATED"

        # ============================================================
        # 8. Disbursement PROCESSING
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

        processing_payload = processing_response.json()

        bank_reference = find_value(
            processing_payload,
            "bank_reference",
        )

        assert bank_reference, (
            "PROCESSING response did not provide "
            f"bank reference: {processing_payload}"
        )

        # ============================================================
        # 9. Bank SUCCESS webhook
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
        # 10. Verify disbursement PROCESSED
        # ============================================================

        disbursement_get_response = client.get(
            f"/disbursements/{disbursement_id}"
        )

        assert_success(
            disbursement_get_response,
            "Disbursement retrieval",
        )

        final_disbursement = (
            disbursement_get_response.json()
        )

        final_status = find_value(
            final_disbursement,
            "status",
        )

        assert final_status == "PROCESSED"

        # Refresh the existing SQLAlchemy session so the
        # repayment-schedule service sees the latest
        # disbursement status persisted by the API request.
        db.expire_all()

        # ============================================================
        # 11. Repayment schedule installment
        # ============================================================

        installment = (
            post_disbursement_service.create_repayment_schedule(
                db=db,
                repayment_schedule_id=repayment_schedule_id,
                application_id=application_id,
                disbursement_id=disbursement_id,
                installment_number=2,
                due_date=datetime(2026, 11, 25),
                principal_due=Decimal("12000.00"),
                interest_due=Decimal("1327.32"),
                total_due=Decimal("13327.32"),
                outstanding_principal=Decimal("126172.68"),
            )

        )

        assert (
            installment.repayment_schedule_id
            == repayment_schedule_id
        )
        assert installment.application_id == application_id
        assert installment.disbursement_id == disbursement_id
        assert installment.installment_number == 2
        assert installment.total_due == Decimal("13327.32")
        assert installment.outstanding_principal == Decimal(
            "126172.68"
        )
        assert installment.status == "PENDING"

    finally:
        db.close()