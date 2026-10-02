import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db

from backend.app.models.disbursement import Disbursement
from backend.app.models.beneficiary_account import BeneficiaryAccount

from backend.app.schemas.disbursement import (
    DisbursementCreate,
    DisbursementResponse,
    DisbursementUpdate,
    DisbursementEligibilityRequest,
    DisbursementEligibilityResponse,
    BankDisbursementWebhook,
)
from backend.app.schemas.beneficiary import (
    BeneficiaryCreate,
    BeneficiaryResponse,
)

from backend.app.services.disbursement_service import disbursement_service
from backend.app.services.disbursement_eligibility_service import disbursement_eligibility_service
from backend.app.services.beneficiary_validation_service import (
    beneficiary_validation_service,
)
from backend.app.services.beneficiary_service import beneficiary_service
from backend.app.services.disbursement_retry_service import (
    disbursement_retry_service,
)
from backend.app.services.reconciliation_service import (
    reconciliation_service,
)
from backend.app.services.audit_log_service import audit_log_service

router = APIRouter(
    prefix="/disbursements",
    tags=["Disbursement"],
)

# Create Beneficiary
@router.post(
    "/beneficiaries",
    response_model=BeneficiaryResponse,
)
def create_beneficiary(
    beneficiary: BeneficiaryCreate,
    db: Session = Depends(get_db),
):
    beneficiary_id = f"BEN-{uuid.uuid4().hex[:12].upper()}"

    result = beneficiary_service.create_beneficiary(
        db=db,
        beneficiary_id=beneficiary_id,
        application_id=beneficiary.application_id,
        account_holder_name=beneficiary.account_holder_name,
        account_number_reference=beneficiary.account_number_reference,
        ifsc_code=beneficiary.ifsc_code,
        bank_name=beneficiary.bank_name,
    )

    return result

# Validate Beneficiary
@router.post(
    "/beneficiaries/{beneficiary_id}/validate"
    )
def validate_beneficiary(
    beneficiary_id: str,
    db: Session = Depends(get_db),
):
    beneficiary = db.get(BeneficiaryAccount, beneficiary_id)

    if beneficiary is None:
        raise HTTPException(
            status_code=404,
            detail="Beneficiary not found",
        )

    result = beneficiary_validation_service.validate_beneficiary(
        db=db,
        beneficiary=beneficiary,
    )

    return {
        "beneficiary_id": result.beneficiary_id,
        "application_id": result.application_id,
        "validation_status": result.validation_status,
        "validation_reference": result.validation_reference,
        "failure_reason": result.failure_reason,
        "validated_at": result.validated_at,
    }

# Check Disbursement Eligibility
@router.post(
    "/eligibility",
    response_model=DisbursementEligibilityResponse,
)
def check_disbursement_eligibility(
    request: DisbursementEligibilityRequest,
    db: Session = Depends(get_db),
):
    return disbursement_eligibility_service.check_eligibility(
        db=db,
        application_id=request.application_id,
        sanction_id=request.sanction_id,
        disbursement_amount=request.disbursement_amount,
    )

# Create Disbursement
@router.post(
    "",
    response_model=DisbursementResponse,
)
def create_disbursement(
    disbursement: DisbursementCreate,
    db: Session = Depends(get_db),
):
    existing_disbursement = (
        db.query(Disbursement)
        .filter(
            Disbursement.idempotency_key == disbursement.idempotency_key
        )
        .first()
    )

    if existing_disbursement is not None:
        return existing_disbursement
        
    disbursement_id = f"DISB-{uuid.uuid4().hex[:12].upper()}"

    result = disbursement_service.create_disbursement(
        db=db,
        disbursement_id=disbursement_id,
        application_id=disbursement.application_id,
        disbursement_amount=disbursement.disbursement_amount,
        status="CREATED",
        idempotency_key=disbursement.idempotency_key,
        sanction_id=disbursement.sanction_id,
        beneficiary_reference=disbursement.beneficiary_reference,
        payment_provider=disbursement.payment_provider,
    )

    return result

# Update Disbursement
@router.post(
    "/{disbursement_id}/status",
    response_model=DisbursementResponse,
)
def update_disbursement_status(
    disbursement_id: str,
    update: DisbursementUpdate,
    db: Session = Depends(get_db),
):
    disbursement = db.get(Disbursement, disbursement_id)

    if disbursement is None:
        raise HTTPException(
            status_code=404,
            detail="Disbursement not found",
        )

    if update.status == "INITIATED":
        return disbursement_service.initiate_disbursement(
            db=db,
            disbursement=disbursement,
        )

    if update.status == "PROCESSING":
        return disbursement_service.mark_processing(
            db=db,
            disbursement=disbursement,
        )

    if update.status == "PROCESSED":
        return disbursement_service.process_disbursement(
            db=db,
            disbursement=disbursement,
            bank_reference=update.bank_reference,
        )

    if update.status == "FAILED":
        return disbursement_service.fail_disbursement(
            db=db,
            disbursement=disbursement,
            failure_reason=update.failure_reason or "Disbursement failed",
        )

    raise HTTPException(
        status_code=400,
        detail="Invalid disbursement status",
    )

# Bank Disbursement Webhook
@router.post("/webhooks/bank")
def bank_disbursement_webhook(
    webhook: BankDisbursementWebhook,
    db: Session = Depends(get_db),
):
    disbursement = db.get(
        Disbursement,
        webhook.disbursement_id,
    )

    if disbursement is None:
        raise HTTPException(
            status_code=404,
            detail="Disbursement not found",
        )

    audit_log_service.log(
        db=db,
        audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
        application_id=disbursement.application_id,
        actor_type="SYSTEM",
        action="BANK_WEBHOOK_RECEIVED",
        entity_type="DISBURSEMENT",
        entity_reference=disbursement.disbursement_id,
        description=(
            f"Bank webhook received with status "
            f"{webhook.status}"
        ),
        previous_state=disbursement.status,
        new_state=webhook.status,
        request_reference=webhook.disbursement_id,
    )

    if disbursement.bank_reference != webhook.bank_reference:
        raise HTTPException(
            status_code=400,
            detail="Bank reference mismatch",
        )

    if webhook.status == "SUCCESS":
        duplicate_webhook = disbursement.status == "PROCESSED"

        if duplicate_webhook:
            result = disbursement
        else:
            result = disbursement_service.process_disbursement(
                db=db,
                disbursement=disbursement,
                bank_reference=webhook.bank_reference,
            )

        reconciliation_result = reconciliation_service.reconcile_disbursement(
            db=db,
            disbursement_id=webhook.disbursement_id,
            bank_reference=webhook.bank_reference,
            bank_amount=webhook.bank_amount,
        )

        return {
            "message": (
                "Duplicate webhook ignored"
                if duplicate_webhook
                else "Disbursement processed successfully"
            ),
            "disbursement_id": result.disbursement_id,
            "status": result.status,
            "bank_reference": result.bank_reference,
            "processed_at": result.processed_at,
            "reconciliation": {
                "status": reconciliation_result.status,
                "bank_amount": reconciliation_result.bank_amount,
                "expected_amount": reconciliation_result.expected_amount,
                "mismatch_reason": reconciliation_result.mismatch_reason,
            },
        }

    if webhook.status == "FAILED":
        result = disbursement_service.fail_disbursement(
            db=db,
            disbursement=disbursement,
            failure_reason=webhook.failure_reason or "Bank disbursement failed",
        )

        return {
            "message": "Disbursement failed",
            "disbursement_id": result.disbursement_id,
            "status": result.status,
            "bank_reference": result.bank_reference,
            "failure_reason": result.failure_reason,
        }

    return {
        "message": "Bank webhook received",
        "disbursement_id": disbursement.disbursement_id,
        "status": disbursement.status,
    }


# Retry Disbursement
@router.post("/{disbursement_id}/retry")
def retry_disbursement(
    disbursement_id: str,
    db: Session = Depends(get_db),
):
    result = disbursement_retry_service.retry_disbursement(
        db=db,
        disbursement_id=disbursement_id,
    )

    if result.get("reason") == "DISBURSEMENT_NOT_FOUND":
        raise HTTPException(
            status_code=404,
            detail="Disbursement not found",
        )

    return result



# Get Disbursement
@router.get(
    "/{disbursement_id}",
    response_model=DisbursementResponse,
)
def get_disbursement(
    disbursement_id: str,
    db: Session = Depends(get_db),
):
    result = db.get(
        Disbursement,
        disbursement_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Disbursement not found",
        )

    return result