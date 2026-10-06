from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.collection import (
    CollectionCreateRequest,
    CollectionResponse,
    CollectionSummaryResponse,
    CollectionRecordRequest,
    CollectionRecordResponse,
    ApplicationOverdueSummaryResponse,
)
from backend.app.schemas.common import ApiResponse
from backend.app.core.responses import success_response
from backend.app.services.collection_service import collection_service
from backend.app.services.overdue_service import overdue_service


router = APIRouter(
    prefix="/collections",
    tags=["Collections"],
)


# ============================================================
# Create Collection
# ============================================================

@router.post(
    "",
    response_model=ApiResponse[CollectionResponse],
)
def create_collection(
    request: CollectionCreateRequest,
    api_request: Request,
    db: Session = Depends(get_db),
):
    try:
        collection = collection_service.create_collection(
            db=db,
            collection_id=f"COLL-{request.repayment_schedule_id[-12:]}",
            application_id=request.application_id,
            repayment_schedule_id=request.repayment_schedule_id,
            collection_type=request.collection_type,
            due_amount=request.due_amount,
            collected_amount=request.collected_amount,
            outstanding_amount=request.outstanding_amount,
            days_past_due=request.days_past_due,
            status=request.status,
            collection_reference=request.collection_reference,
            collection_channel=request.collection_channel,
            remarks=request.remarks,
            collected_at=request.collected_at,
        )

        response_data = CollectionResponse.model_validate(
            collection
        )

        return success_response(
            request=api_request,
            data=response_data,
            message="Collection created successfully.",
        )

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# Record Collection
# ============================================================

@router.post(
    "/record",
    response_model=ApiResponse[CollectionRecordResponse],
)
def record_collection(
    request: CollectionRecordRequest,
    api_request: Request,
    db: Session = Depends(get_db),
):
    try:
        collection = collection_service.record_collection(
            db=db,
            collection_id=f"COLL-{request.repayment_schedule_id[-12:]}",
            application_id=request.application_id,
            repayment_schedule_id=request.repayment_schedule_id,
            repayment_amount=request.repayment_amount,
            collection_reference=request.collection_reference,
            collection_channel=request.collection_channel,
            payment_mode=request.payment_mode,
            payment_provider=request.payment_provider,
            remarks=request.remarks,
        )

        response_data = CollectionRecordResponse.model_validate(
            collection
        )

        return success_response(
            request=api_request,
            data=response_data,
            message="Collection recorded successfully.",
        )

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# Get Overdue Schedules
# IMPORTANT: keep before /{application_id}
# ============================================================

@router.get(
    "/overdue",
    response_model=ApiResponse[Any],
)
def get_overdue_schedules(
    api_request: Request,
    reference_date: datetime | None = None,
    db: Session = Depends(get_db),
):
    if reference_date is None:
        reference_date = datetime.utcnow()

    result = overdue_service.get_overdue_schedules(
        db=db,
        reference_date=reference_date,
    )

    return success_response(
        request=api_request,
        data=result,
        message="Overdue schedules retrieved successfully.",
    )


# ============================================================
# Get Collections by Application
# ============================================================

@router.get(
    "/{application_id}",
    response_model=ApiResponse[list[CollectionResponse]],
)
def get_collections_by_application(
    application_id: str,
    api_request: Request,
    db: Session = Depends(get_db),
):
    try:
        result = collection_service.get_collections_by_application(
            db=db,
            application_id=application_id,
        )

        response_data = [
            CollectionResponse.model_validate(item)
            for item in result
        ]

        return success_response(
            request=api_request,
            data=response_data,
            message="Application collections retrieved successfully.",
        )

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# Get Collections by Repayment Schedule
# ============================================================

@router.get(
    "/{application_id}/{repayment_schedule_id}",
    response_model=ApiResponse[list[CollectionResponse]],
)
def get_collections_by_schedule(
    application_id: str,
    repayment_schedule_id: str,
    api_request: Request,
    db: Session = Depends(get_db),
):
    try:
        result = collection_service.get_collections_by_schedule(
            db=db,
            application_id=application_id,
            repayment_schedule_id=repayment_schedule_id,
        )

        response_data = [
            CollectionResponse.model_validate(item)
            for item in result
        ]

        return success_response(
            request=api_request,
            data=response_data,
            message="Schedule collections retrieved successfully.",
        )

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# Get Collection Summary
# ============================================================

@router.get(
    "/{application_id}/{repayment_schedule_id}/summary",
    response_model=ApiResponse[CollectionSummaryResponse],
)
def get_collection_summary(
    application_id: str,
    repayment_schedule_id: str,
    api_request: Request,
    db: Session = Depends(get_db),
):
    try:
        result = collection_service.get_collection_summary(
            db=db,
            application_id=application_id,
            repayment_schedule_id=repayment_schedule_id,
        )

        response_data = CollectionSummaryResponse.model_validate(
            result
        )

        return success_response(
            request=api_request,
            data=response_data,
            message="Collection summary retrieved successfully.",
        )

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# Get Application Overdue Summary
# ============================================================

@router.get(
    "/{application_id}/overdue-summary",
    response_model=ApiResponse[ApplicationOverdueSummaryResponse],
)
def get_application_overdue_summary(
    application_id: str,
    api_request: Request,
    reference_date: datetime | None = None,
    db: Session = Depends(get_db),
):
    if reference_date is None:
        reference_date = datetime.utcnow()

    try:
        result = overdue_service.get_application_overdue_summary(
            db=db,
            application_id=application_id,
            reference_date=reference_date,
        )

        response_data = (
            ApplicationOverdueSummaryResponse.model_validate(
                result
            )
        )

        return success_response(
            request=api_request,
            data=response_data,
            message="Application overdue summary retrieved successfully.",
        )

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )