import uuid
from typing import Any

from functools import wraps
from inspect import signature

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

from backend.app.core.workflow_logging import log_workflow_event
from backend.app.core.responses import success_response
from backend.app.core.security import require_roles

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

def _get_path_value(source: Any, path: str | None) -> Any:
    """Read a nested field from a dictionary or object safely."""
    if source is None or not path:
        return None

    value = source

    for part in path.split("."):
        if value is None:
            return None

        if isinstance(value, dict):
            value = value.get(part)
        else:
            value = getattr(value, part, None)

    return value


def log_disbursement_lifecycle(
    *,
    workflow: str,
    entity_type: str,
    error_code: str,
    application_id_source: str | None = None,
    entity_id_source: str | None = None,
    response_application_id_field: str | None = None,
    response_entity_id_field: str | None = None,
):
    """Log lifecycle events while preserving the route's original behavior."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            bound = signature(func).bind_partial(*args, **kwargs)
            arguments = bound.arguments

            request = arguments.get("request")

            # Do not interfere with an invocation that has no Request object.
            if request is None:
                return func(*args, **kwargs)

            application_id = _get_path_value(
                arguments,
                application_id_source,
            )
            entity_id = _get_path_value(
                arguments,
                entity_id_source,
            )

            log_workflow_event(
                workflow=workflow,
                event="started",
                request=request,
                application_id=application_id,
                entity_type=entity_type,
                entity_id=entity_id,
            )

            try:
                response = func(*args, **kwargs)
            except Exception:
                log_workflow_event(
                    workflow=workflow,
                    event="failed",
                    request=request,
                    application_id=application_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    error_code=error_code,
                )
                raise

            # Resolve identifiers generated or returned by the route.
            if response_application_id_field:
                returned_application_id = _get_path_value(
                    response,
                    f"data.{response_application_id_field}",
                )
                if returned_application_id is not None:
                    application_id = returned_application_id

            if response_entity_id_field:
                returned_entity_id = _get_path_value(
                    response,
                    f"data.{response_entity_id_field}",
                )
                if returned_entity_id is not None:
                    entity_id = returned_entity_id

            log_workflow_event(
                workflow=workflow,
                event="completed",
                request=request,
                application_id=application_id,
                entity_type=entity_type,
                entity_id=entity_id,
                status="COMPLETED",
            )

            return response

        return wrapper

    return decorator


# ============================================================
# Create Beneficiary
# ============================================================

@router.post(
    "/beneficiaries",
    response_model=ApiResponse[BeneficiaryResponse],
    dependencies=[
        Depends(require_roles("ADMIN", "OPERATIONS", "CREDIT_OFFICER"))
    ],
)
@log_disbursement_lifecycle(
    workflow="beneficiary_creation",
    entity_type="beneficiary",
    application_id_source="beneficiary.application_id",
    response_entity_id_field="beneficiary_id",
    error_code="BENEFICIARY_CREATION_FAILED",
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
    dependencies=[
        Depends(require_roles("ADMIN", "OPERATIONS", "CREDIT_OFFICER"))
    ],
)
@log_disbursement_lifecycle(
    workflow="beneficiary_validation",
    entity_type="beneficiary",
    entity_id_source="beneficiary_id",
    response_application_id_field="application_id",
    error_code="BENEFICIARY_VALIDATION_FAILED",
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
    dependencies=[
        Depends(
            require_roles(
                "ADMIN",
                "CREDIT_ANALYST",
                "CREDIT_OFFICER",
                "OPERATIONS",
                "RISK",
            )
        )
    ],
)
@log_disbursement_lifecycle(
    workflow="disbursement_eligibility_check",
    entity_type="disbursement_eligibility",
    application_id_source="eligibility_request.application_id",
    entity_id_source="eligibility_request.application_id",
    error_code="DISBURSEMENT_ELIGIBILITY_CHECK_FAILED",
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
    dependencies=[Depends(require_roles("ADMIN", "OPERATIONS"))],
)
@log_disbursement_lifecycle(
    workflow="disbursement_creation",
    entity_type="disbursement",
    application_id_source="disbursement.application_id",
    response_entity_id_field="disbursement_id",
    error_code="DISBURSEMENT_CREATION_FAILED",
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
    dependencies=[Depends(require_roles("ADMIN", "OPERATIONS"))],
)
def update_disbursement_status(
    disbursement_id: str,
    update: DisbursementUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    log_workflow_event(
        workflow="disbursement_status_update",
        event="started",
        request=request,
        entity_type="disbursement",
        entity_id=disbursement_id,
        status=update.status,
    )

    disbursement = db.get(
        Disbursement,
        disbursement_id,
    )

    if disbursement is None:
        log_workflow_event(
            workflow="disbursement_status_update",
            event="failed",
            request=request,
            entity_type="disbursement",
            entity_id=disbursement_id,
            status=update.status,
            error_code="DISBURSEMENT_NOT_FOUND",
        )

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

        log_workflow_event(
            workflow="disbursement_status_update",
            event="completed",
            request=request,
            entity_type="disbursement",
            entity_id=disbursement_id,
            status=update.status,
        )

        return success_response(
            request=request,
            data=response_data,
            message="Disbursement status updated successfully.",
        )

    except HTTPException:
        log_workflow_event(
            workflow="disbursement_status_update",
            event="failed",
            request=request,
            entity_type="disbursement",
            entity_id=disbursement_id,
            status=update.status,
            error_code="DISBURSEMENT_STATUS_UPDATE_REJECTED",
        )
        raise

    except ValueError as exc:
        log_workflow_event(
            workflow="disbursement_status_update",
            event="failed",
            request=request,
            entity_type="disbursement",
            entity_id=disbursement_id,
            status=update.status,
            error_code="DISBURSEMENT_STATUS_UPDATE_FAILED",
        )

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        log_workflow_event(
            workflow="disbursement_status_update",
            event="failed",
            request=request,
            entity_type="disbursement",
            entity_id=disbursement_id,
            status=update.status,
            error_code="DISBURSEMENT_STATUS_UPDATE_FAILED",
        )
        raise


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
    disbursement_id = webhook.disbursement_id

    log_workflow_event(
        workflow="bank_disbursement_webhook",
        event="started",
        request=request,
        entity_type="disbursement",
        entity_id=disbursement_id,
    )

    try:
        disbursement = db.get(
            Disbursement,
            disbursement_id,
        )

        if disbursement is None:
            log_workflow_event(
                workflow="bank_disbursement_webhook",
                event="failed",
                request=request,
                entity_type="disbursement",
                entity_id=disbursement_id,
                error_code="DISBURSEMENT_NOT_FOUND",
            )

            raise HTTPException(
                status_code=404,
                detail="Disbursement not found",
            )

        response_data = {
            "message": "Bank webhook received",
            "disbursement_id": disbursement.disbursement_id,
            "status": disbursement.status,
        }

    except HTTPException:
        raise

    except Exception:
        log_workflow_event(
            workflow="bank_disbursement_webhook",
            event="failed",
            request=request,
            entity_type="disbursement",
            entity_id=disbursement_id,
            error_code="BANK_DISBURSEMENT_WEBHOOK_FAILED",
        )
        raise

    if disbursement.bank_reference != webhook.bank_reference:
        log_workflow_event(
            workflow="bank_disbursement_webhook",
            event="failed",
            request=request,
            entity_type="disbursement",
            entity_id=disbursement_id,
            error_code="BANK_REFERENCE_MISMATCH",
    )
        raise HTTPException(
            status_code=400,
            detail="Bank reference mismatch",
        )

    if webhook.status not in {"SUCCESS", "FAILED"}:
        log_workflow_event(
            workflow="bank_disbursement_webhook",
            event="failed",
            request=request,
            entity_type="disbursement",
            entity_id=disbursement_id,
            error_code="INVALID_BANK_WEBHOOK_STATUS",
        )
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

    # Persist receipt independently of the later payment outcome.
    # This ensures duplicate callbacks are also durably audited.
    db.commit()

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
                log_workflow_event(
                    workflow="bank_disbursement_webhook",
                    event="failed",
                    request=request,
                    entity_type="disbursement",
                    entity_id=disbursement_id,
                    error_code="BANK_DISBURSEMENT_PROCESSING_FAILED",
                )
                
                raise HTTPException(
                    status_code=409,
                    detail=str(exc),
                )

            except Exception:
                log_workflow_event(
                    workflow="bank_disbursement_webhook",
                    event="failed",
                    request=request,
                    entity_type="disbursement",
                    entity_id=disbursement_id,
                    error_code="BANK_DISBURSEMENT_PROCESSING_FAILED",
                )
                raise

        try:
            reconciliation_result = (
                reconciliation_service.reconcile_disbursement(
                    db=db,
                    disbursement_id=webhook.disbursement_id,
                    bank_reference=webhook.bank_reference,
                    bank_amount=webhook.bank_amount,
                )
            )

        except Exception:
            log_workflow_event(
                workflow="bank_disbursement_webhook",
                event="failed",
                request=request,
                entity_type="disbursement",
                entity_id=disbursement_id,
                error_code="BANK_WEBHOOK_RECONCILIATION_FAILED",
            )
            raise

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

        log_workflow_event(
            workflow="bank_disbursement_webhook",
            event="completed",
            request=request,
            entity_type="disbursement",
            entity_id=disbursement_id,
            status=result.status,
        )

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

        log_workflow_event(
            workflow="bank_disbursement_webhook",
            event="completed",
            request=request,
            entity_type="disbursement",
            entity_id=disbursement_id,
            status="FAILED",
        )

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
            log_workflow_event(
                workflow="bank_disbursement_webhook",
                event="failed",
                request=request,
                entity_type="disbursement",
                entity_id=disbursement_id,
                error_code="BANK_DISBURSEMENT_FAILURE_UPDATE_FAILED",
            )
            raise HTTPException(
                status_code=409,
                detail=str(exc),
            )

        except Exception:
            log_workflow_event(
                workflow="bank_disbursement_webhook",
                event="failed",
                request=request,
                entity_type="disbursement",
                entity_id=disbursement_id,
                error_code="BANK_DISBURSEMENT_FAILURE_UPDATE_FAILED",
            )
            raise

        response_data = {
            "message": "Disbursement failed",
            "disbursement_id": result.disbursement_id,
            "status": result.status,
            "bank_reference": result.bank_reference,
            "failure_reason": result.failure_reason,
        }

        log_workflow_event(
            workflow="bank_disbursement_webhook",
            event="completed",
            request=request,
            entity_type="disbursement",
            entity_id=disbursement_id,
            status=result.status,
        )

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

    log_workflow_event(
        workflow="bank_disbursement_webhook",
        event="completed",
        request=request,
        entity_type="disbursement",
        entity_id=disbursement_id,
        status=disbursement.status,
    )

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
    dependencies=[Depends(require_roles("ADMIN", "OPERATIONS"))],
)
def retry_disbursement(
    disbursement_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    log_workflow_event(
        workflow="disbursement_retry",
        event="started",
        request=request,
        entity_type="disbursement",
        entity_id=disbursement_id,
    )

    try:
        result = disbursement_retry_service.retry_disbursement(
            db=db,
            disbursement_id=disbursement_id,
        )

    except Exception:
        log_workflow_event(
            workflow="disbursement_retry",
            event="failed",
            request=request,
            entity_type="disbursement",
            entity_id=disbursement_id,
            error_code="DISBURSEMENT_RETRY_FAILED",
        )
        raise

    if result.get("reason") == "DISBURSEMENT_NOT_FOUND":
        log_workflow_event(
            workflow="disbursement_retry",
            event="failed",
            request=request,
            entity_type="disbursement",
            entity_id=disbursement_id,
            error_code="DISBURSEMENT_NOT_FOUND",
        )

        raise HTTPException(
            status_code=404,
            detail="Disbursement not found",
        )

    log_workflow_event(
        workflow="disbursement_retry",
        event="completed",
        request=request,
        entity_type="disbursement",
        entity_id=disbursement_id,
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
    dependencies=[
        Depends(
            require_roles(
                "ADMIN",
                "OPERATIONS",
                "CREDIT_ANALYST",
                "CREDIT_OFFICER",
                "RISK",
                "AUDITOR",
            )
        )
    ],
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