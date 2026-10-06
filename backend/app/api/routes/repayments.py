import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.repayment import (
    RepaymentScheduleGenerateRequest,
    RepaymentScheduleResponse,
    RepaymentCreateRequest,
    RepaymentResponse,
    RepaymentSummaryResponse,
)
from backend.app.schemas.common import ApiResponse
from backend.app.core.responses import success_response

from backend.app.services.repayment_schedule_service import (
    repayment_schedule_service,
)
from backend.app.services.repayment_service import repayment_service


router = APIRouter(
    prefix="/repayments",
    tags=["Repayment"],
)


# ============================================================
# Generate Repayment Schedule
# ============================================================

@router.post(
    "/schedule",
    response_model=ApiResponse[list[RepaymentScheduleResponse]],
)
def generate_repayment_schedule(
    request: RepaymentScheduleGenerateRequest,
    api_request: Request,
    db: Session = Depends(get_db),
):
    try:
        schedule = repayment_schedule_service.generate_schedule(
            db=db,
            application_id=request.application_id,
            disbursement_id=request.disbursement_id,
            principal=request.principal,
            annual_interest_rate=request.annual_interest_rate,
            tenure_months=request.tenure_months,
            first_due_date=request.first_due_date,
        )

        response_data = [
            RepaymentScheduleResponse.model_validate(item)
            for item in schedule
        ]

        return success_response(
            request=api_request,
            data=response_data,
            message="Repayment schedule generated successfully.",
        )

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# Record Repayment
# ============================================================

@router.post(
    "/record",
    response_model=ApiResponse[RepaymentResponse],
)
def record_repayment(
    request: RepaymentCreateRequest,
    api_request: Request,
    db: Session = Depends(get_db),
):
    try:
        repayment = repayment_service.record_repayment(
            db=db,
            repayment_id=f"REP-{uuid.uuid4().hex[:12].upper()}",
            application_id=request.application_id,
            repayment_schedule_id=request.repayment_schedule_id,
            repayment_amount=request.repayment_amount,
            repayment_reference=request.repayment_reference,
            payment_mode=request.payment_mode,
            payment_provider=request.payment_provider,
        )

        response_data = RepaymentResponse.model_validate(
            repayment
        )

        return success_response(
            request=api_request,
            data=response_data,
            message="Repayment recorded successfully.",
        )

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# Get Repayment Schedule
# ============================================================

@router.get(
    "/schedule/{application_id}/{disbursement_id}",
    response_model=ApiResponse[list[RepaymentScheduleResponse]],
)
def get_repayment_schedule_by_disbursement(
    application_id: str,
    disbursement_id: str,
    api_request: Request,
    db: Session = Depends(get_db),
):
    try:
        schedule = (
            repayment_schedule_service.get_schedule_by_disbursement(
                db=db,
                application_id=application_id,
                disbursement_id=disbursement_id,
            )
        )

        response_data = [
            RepaymentScheduleResponse.model_validate(item)
            for item in schedule
        ]

        return success_response(
            request=api_request,
            data=response_data,
            message="Repayment schedule retrieved successfully.",
        )

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# Get Repayment Summary
# ============================================================

@router.get(
    "/summary/{application_id}/{disbursement_id}",
    response_model=ApiResponse[RepaymentSummaryResponse],
)
def get_repayment_summary(
    application_id: str,
    disbursement_id: str,
    api_request: Request,
    db: Session = Depends(get_db),
):
    try:
        summary = repayment_schedule_service.get_repayment_summary(
            db=db,
            application_id=application_id,
            disbursement_id=disbursement_id,
        )

        response_data = RepaymentSummaryResponse.model_validate(
            summary
        )

        return success_response(
            request=api_request,
            data=response_data,
            message="Repayment summary retrieved successfully.",
        )

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )