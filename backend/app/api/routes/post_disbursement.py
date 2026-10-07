from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.common import ApiResponse
from backend.app.core.responses import success_response
from backend.app.services.reconciliation_service import (
    reconciliation_service,
)


router = APIRouter(
    prefix="/reconciliation",
    tags=["Reconciliation"],
)


# ============================================================
# Reconciliation Check
# ============================================================

@router.post(
    "/check",
    response_model=ApiResponse[dict[str, Any]],
)
def check_reconciliation(
    disbursement_id: str,
    request: Request,
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

    response_data = {
        "status": result.status,
        "disbursement_id": result.disbursement_id,
        "bank_reference": result.bank_reference,
        "bank_amount": result.bank_amount,
        "expected_amount": result.expected_amount,
        "mismatch_reason": result.mismatch_reason,
    }

    return success_response(
        request=request,
        data=response_data,
        message="Reconciliation check completed successfully.",
    )


# ============================================================
# Close Reconciliation
# ============================================================

@router.post(
    "/close",
    response_model=ApiResponse[dict[str, Any]],
)
def close_reconciliation(
    reconciliation_id: str,
    request: Request,
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

    response_data = {
        "reconciliation_id": result.reconciliation_id,
        "disbursement_id": result.disbursement_id,
        "reconciliation_status": result.reconciliation_status,
        "reconciled_at": result.reconciled_at,
    }

    return success_response(
        request=request,
        data=response_data,
        message="Reconciliation closed successfully.",
    )