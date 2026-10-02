from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
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
from backend.app.services.collection_service import collection_service
from backend.app.services.overdue_service import overdue_service


router = APIRouter(
    prefix="/collections",
    tags=["Collections"],
)


@router.post(
    "",
    response_model=CollectionResponse,
)
def create_collection(
    request: CollectionCreateRequest,
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

        return collection

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.post(
    "/record",
    response_model=CollectionRecordResponse,
)
def record_collection(
    request: CollectionRecordRequest,
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

        return collection

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.get(
    "/{application_id}",
    response_model=list[CollectionResponse],
)
def get_collections_by_application(
    application_id: str,
    db: Session = Depends(get_db),
):
    try:
        return collection_service.get_collections_by_application(
            db=db,
            application_id=application_id,
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.get(
    "/{application_id}/{repayment_schedule_id}",
    response_model=list[CollectionResponse],
)
def get_collections_by_schedule(
    application_id: str,
    repayment_schedule_id: str,
    db: Session = Depends(get_db),
):
    try:
        return collection_service.get_collections_by_schedule(
            db=db,
            application_id=application_id,
            repayment_schedule_id=repayment_schedule_id,
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.get(
    "/{application_id}/{repayment_schedule_id}/summary",
    response_model=CollectionSummaryResponse,
)
def get_collection_summary(
    application_id: str,
    repayment_schedule_id: str,
    db: Session = Depends(get_db),
):
    try:
        return collection_service.get_collection_summary(
            db=db,
            application_id=application_id,
            repayment_schedule_id=repayment_schedule_id,
        )

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get("/overdue")
def get_overdue_schedules(
    reference_date: datetime | None = None,
    db: Session = Depends(get_db),
):
    if reference_date is None:
        reference_date = datetime.utcnow()

    return overdue_service.get_overdue_schedules(
        db=db,
        reference_date=reference_date,
    )

@router.get(
    "/{application_id}/overdue-summary",
    response_model=ApplicationOverdueSummaryResponse,
)
def get_application_overdue_summary(
    application_id: str,
    reference_date: datetime | None = None,
    db: Session = Depends(get_db),
):
    if reference_date is None:
        reference_date = datetime.utcnow()

    try:
        return overdue_service.get_application_overdue_summary(
            db=db,
            application_id=application_id,
            reference_date=reference_date,
        )

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )