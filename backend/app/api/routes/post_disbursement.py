from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db

from backend.app.services.reconciliation_service import reconciliation_service

router = APIRouter(
    prefix="/post-disbursement",
    tags=["Reconciliation"],
)


@router.post("/reconciliation/check")
def check_reconciliation(
    disbursement_id: str,
    bank_reference: str | None = None,
    bank_amount: Decimal | None = None,
    db: Session = Depends(get_db),
):
    result = reconciliation_service.reconcile_disbursement(
        db=db,
        disbursement_id=disbursement_id,
        bank_reference=bank_reference,
        bank_amount=bank_amount,
    )

    return {
        "status": result.status,
        "disbursement_id": result.disbursement_id,
        "bank_reference": result.bank_reference,
        "bank_amount": result.bank_amount,
        "expected_amount": result.expected_amount,
        "mismatch_reason": result.mismatch_reason,
    }

@router.post("/reconciliation/close")
def close_reconciliation(
    reconciliation_id: str,
    db: Session = Depends(get_db),
):
    try:
        result = reconciliation_service.close_reconciliation(
            db=db,
            reconciliation_id=reconciliation_id,
        )

    except ValueError as exc:
        if str(exc) == "RECONCILIATION_NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail="Reconciliation not found",
            )

        if str(exc) == "RECONCILIATION_NOT_MATCHED":
            raise HTTPException(
                status_code=400,
                detail="Reconciliation is not in MATCHED status",
            )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "message": "Reconciliation closed successfully",
        "reconciliation_id": result.reconciliation_id,
        "disbursement_id": result.disbursement_id,
        "reconciliation_status": result.reconciliation_status,
        "reconciled_at": result.reconciled_at,
    }

@router.post("/operations-queue")
def update_operations_queue_status(
    queue_id: str,
    queue_status: str,
    db: Session = Depends(get_db),
):
    try:
        result = reconciliation_service.update_operations_queue_status(
            db=db,
            queue_id=queue_id,
            queue_status=queue_status,
        )

    except ValueError as exc:
        if str(exc) == "OPERATIONS_QUEUE_NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail="Operations queue item not found",
            )

        if str(exc) == "INVALID_OPERATIONS_QUEUE_STATUS":
            raise HTTPException(
                status_code=400,
                detail="Invalid operations queue status",
            )

        if str(exc) == "OPERATIONS_QUEUE_ALREADY_RESOLVED":
            raise HTTPException(
                status_code=400,
                detail="Operations queue item is already resolved",
            )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "message": "Operations queue status updated successfully",
        "queue_id": result.queue_id,
        "reconciliation_id": result.reconciliation_id,
        "disbursement_id": result.disbursement_id,
        "queue_type": result.queue_type,
        "queue_status": result.queue_status,
        "reason": result.reason,
    }