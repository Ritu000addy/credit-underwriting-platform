import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
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

from backend.app.schemas.common import ApiResponse
from backend.app.core.responses import success_response

from backend.app.services.disbursement_service import disbursement_service
from backend.app.services.disbursement_eligibility_service import (
    disbursement_eligibility_service,
)
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


# ============================================================
# Create Beneficiary
# ============================================================

@router.post(
    "/beneficiaries",
    response_model=ApiResponse[BeneficiaryResponse],
)
def create_beneficiary(
    beneficiary: BeneficiaryCreate,
    request: Request,
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

    response_data = BeneficiaryResponse.model_validate(result)

    return success_response(
        request=request,
        data=response_data,
        message="Beneficiary created successfully.",
    )


# ============================================================
# Validate Beneficiary
# ============================================================

@router.post(
    "/beneficiaries/{beneficiary_id}/validate",
    response_model=ApiResponse[dict[str, Any]],
)
def validate_beneficiary(
    beneficiary_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    beneficiary = db.get(
        BeneficiaryAccount,
        beneficiary_id,
    )

    if beneficiary is None:
        raise HTTPException(
            status_code=404,
            detail="Beneficiary not found",
        )

    try:
        result = beneficiary_validation_service.validate_beneficiary(
            db=db,
            beneficiary=beneficiary,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    response_data = {
        "beneficiary_id": result.beneficiary_id,
        "application_id": result.application_id,
        "validation_status": result.validation_status,
        "validation_reference": result.validation_reference,
        "failure_reason": result.failure_reason,
        "validated_at": result.validated_at,
    }

    return success_response(
        request=request,
        data=response_data,
        message="Beneficiary validation completed successfully.",
    )


# ============================================================
# Check Disbursement Eligibility
# ============================================================

@router.post(
    "/eligibility",
    response_model=ApiResponse[DisbursementEligibilityResponse],
)
def check_disbursement_eligibility(
    eligibility_request: DisbursementEligibilityRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    result = disbursement_eligibility_service.check_eligibility(
        db=db,
        application_id=eligibility_request.application_id,
        sanction_id=eligibility_request.sanction_id,
        disbursement_amount=eligibility_request.disbursement_amount,
        beneficiary_reference=eligibility_request.beneficiary_reference,
    )

    response_data = DisbursementEligibilityResponse.model_validate(
        result
    )

    return success_response(
        request=request,
        data=response_data,
        message="Disbursement eligibility checked successfully.",
    )


# ============================================================
# Create Disbursement
# ============================================================

@router.post(
    "",
    response_model=ApiResponse[DisbursementResponse],
)
def create_disbursement(
    disbursement: DisbursementCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    existing_disbursement = (
        db.query(Disbursement)
        .filter(
            Disbursement.idempotency_key
            == disbursement.idempotency_key
        )
        .first()
    )

    if existing_disbursement is not None:

        same_request = (
            existing_disbursement.application_id
            == disbursement.application_id
            and existing_disbursement.sanction_id
            == disbursement.sanction_id
            and existing_disbursement.disbursement_amount
            == disbursement.disbursement_amount
            and existing_disbursement.beneficiary_reference
            == disbursement.beneficiary_reference
            and existing_disbursement.payment_provider
            == disbursement.payment_provider
        )

        if not same_request:
            raise HTTPException(
                status_code=409,
                detail="IDEMPOTENCY_KEY_PAYLOAD_MISMATCH",
            )

        response_data = DisbursementResponse.model_validate(
            existing_disbursement
        )

        return success_response(
            request=request,
            data=response_data,
            message="Existing disbursement returned for idempotent request.",
        )

    eligibility = (
        disbursement_eligibility_service.check_eligibility(
            db=db,
            application_id=disbursement.application_id,
            sanction_id=disbursement.sanction_id,
            disbursement_amount=disbursement.disbursement_amount,
            beneficiary_reference=disbursement.beneficiary_reference,
        )
    )

    if not eligibility["eligible"]:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "DISBURSEMENT_NOT_ELIGIBLE",
                "reasons": eligibility["reasons"],
            },
        )

    disbursement_id = (
        f"DISB-{uuid.uuid4().hex[:12].upper()}"
    )

    try:
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

        response_data = DisbursementResponse.model_validate(result)

        return success_response(
            request=request,
            data=response_data,
            message="Disbursement created successfully.",
        )

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except IntegrityError:
        db.rollback()

        existing_disbursement = (
            db.query(Disbursement)
            .filter(
                Disbursement.idempotency_key
                == disbursement.idempotency_key
            )
            .first()
        )

        if existing_disbursement is None:
            raise HTTPException(
                status_code=409,
                detail="DISBURSEMENT_CREATE_CONFLICT",
            )

        same_request = (
            existing_disbursement.application_id
            == disbursement.application_id
            and existing_disbursement.sanction_id
            == disbursement.sanction_id
            and existing_disbursement.disbursement_amount
            == disbursement.disbursement_amount
            and existing_disbursement.beneficiary_reference
            == disbursement.beneficiary_reference
            and existing_disbursement.payment_provider
            == disbursement.payment_provider
        )

        if not same_request:
            raise HTTPException(
                status_code=409,
                detail="IDEMPOTENCY_KEY_PAYLOAD_MISMATCH",
            )

        response_data = DisbursementResponse.model_validate(
            existing_disbursement
        )

        return success_response(
            request=request,
            data=response_data,
            message="Existing disbursement returned after idempotency conflict.",
        )


# ============================================================
# Update Disbursement
# ============================================================

@router.post(
    "/{disbursement_id}/status",
    response_model=ApiResponse[DisbursementResponse],
)
def update_disbursement_status(
    disbursement_id: str,
    update: DisbursementUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    disbursement = db.get(
        Disbursement,
        disbursement_id,
    )

    if disbursement is None:
        raise HTTPException(
            status_code=404,
            detail="Disbursement not found",
        )

    try:
        if update.status == "INITIATED":
            result = disbursement_service.initiate_disbursement(
                db=db,
                disbursement=disbursement,
            )

        elif update.status == "PROCESSING":
            result = disbursement_service.mark_processing(
                db=db,
                disbursement=disbursement,
            )

        elif update.status == "PROCESSED":
            result = disbursement_service.process_disbursement(
                db=db,
                disbursement=disbursement,
                bank_reference=update.bank_reference,
            )

        elif update.status == "FAILED":
            result = disbursement_service.fail_disbursement(
                db=db,
                disbursement=disbursement,
                failure_reason=(
                    update.failure_reason
                    or "Disbursement failed"
                ),
            )

        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid disbursement status",
            )

        response_data = DisbursementResponse.model_validate(result)

        return success_response(
            request=request,
            data=response_data,
            message="Disbursement status updated successfully.",
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )


# ============================================================
# Bank Disbursement Webhook
# ============================================================

@router.post(
    "/webhooks/bank",
    response_model=ApiResponse[dict[str, Any]],
)
def bank_disbursement_webhook(
    webhook: BankDisbursementWebhook,
    request: Request,
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

    if disbursement.bank_reference != webhook.bank_reference:
        raise HTTPException(
            status_code=400,
            detail="Bank reference mismatch",
        )

    if webhook.status not in {"SUCCESS", "FAILED"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid bank webhook status",
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

    if webhook.status == "SUCCESS":
        duplicate_webhook = disbursement.status == "PROCESSED"

        if duplicate_webhook:
            result = disbursement
        else:
            try:
                if disbursement.status == "INITIATED":
                    disbursement = (
                        disbursement_service.mark_processing(
                            db=db,
                            disbursement=disbursement,
                        )
                    )

                if disbursement.status != "PROCESSING":
                    raise ValueError(
                        "DISBURSEMEN_NOT_READY_FOR_BANK_SUCCESS"
                    )

                result = (
                    disbursement_service.process_disbursement(
                        db=db,
                        disbursement=disbursement,
                        bank_reference=webhook.bank_reference,
                    )
                )

            except ValueError as exc:
                raise HTTPException(
                    status_code=409,
                    detail=str(exc),
                )

        reconciliation_result = (
            reconciliation_service.reconcile_disbursement(
                db=db,
                disbursement_id=webhook.disbursement_id,
                bank_reference=webhook.bank_reference,
                bank_amount=webhook.bank_amount,
            )
        )

        response_data = {
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

        return success_response(
            request=request,
            data=response_data,
            message=(
                "Duplicate bank webhook handled."
                if duplicate_webhook
                else "Bank disbursement processed successfully."
            ),
        )

    if disbursement.status == "FAILED":
        response_data = {
            "disbursement_id": disbursement.disbursement_id,
            "status": "FAILED",
            "bank_reference": disbursement.bank_reference,
            "failure_reason": disbursement.failure_reason,
            "duplicate_webhook": True,
        }

        return success_response(
            request=request,
            data=response_data,
            message="Duplicate failed bank webhook ignored.",
        )

    if webhook.status == "FAILED":
        try:
            result = disbursement_service.fail_disbursement(
                db=db,
                disbursement=disbursement,
                failure_reason=(
                    webhook.failure_reason
                    or "Bank disbursement failed"
                ),
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=409,
                detail=str(exc),
            )

        response_data = {
            "message": "Disbursement failed",
            "disbursement_id": result.disbursement_id,
            "status": result.status,
            "bank_reference": result.bank_reference,
            "failure_reason": result.failure_reason,
        }

        return success_response(
            request=request,
            data=response_data,
            message="Bank disbursement failure processed successfully.",
        )

    response_data = {
        "message": "Bank webhook received",
        "disbursement_id": disbursement.disbursement_id,
        "status": disbursement.status,
    }

    return success_response(
        request=request,
        data=response_data,
        message="Bank webhook received successfully.",
    )


# ============================================================
# Retry Disbursement
# ============================================================

@router.post(
    "/{disbursement_id}/retry",
    response_model=ApiResponse[dict[str, Any]],
)
def retry_disbursement(
    disbursement_id: str,
    request: Request,
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

    return success_response(
        request=request,
        data=result,
        message="Disbursement retry processed successfully.",
    )


# ============================================================
# Get Disbursement
# ============================================================

@router.get(
    "/{disbursement_id}",
    response_model=ApiResponse[DisbursementResponse],
)
def get_disbursement(
    disbursement_id: str,
    request: Request,
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

    response_data = DisbursementResponse.model_validate(result)

    return success_response(
        request=request,
        data=response_data,
        message="Disbursement retrieved successfully.",
    )