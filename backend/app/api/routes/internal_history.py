from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.internal_history import InternalHistoryCreate
from backend.app.services.internal_history_service import internal_history_service


router = APIRouter(
    prefix="/internal-history",
    tags=["Source Data Ingestion"],
)


@router.post("")
def create_internal_history(
    history: InternalHistoryCreate,
    db: Session = Depends(get_db),
):
    result = internal_history_service.create_internal_history(
        db=db,
        history=history,
    )

    return {
        "message": "Internal loan history created successfully",
        "internal_history": {
            "internal_history_id": result.internal_history_id,
            "application_id": result.application_id,
            "previous_loans_count": result.previous_loans_count,
            "active_loans_count": result.active_loans_count,
            "closed_loans_count": result.closed_loans_count,
            "total_previous_exposure": result.total_previous_exposure,
            "total_outstanding_amount": result.total_outstanding_amount,
            "repayment_history": result.repayment_history,
            "dpd_count": result.dpd_count,
            "max_dpd": result.max_dpd,
            "overdue_amount": result.overdue_amount,
            "write_off_count": result.write_off_count,
            "settlement_count": result.settlement_count,
            "last_loan_date": result.last_loan_date,
            "analysis_reference": result.analysis_reference,
            "analyzed_at": result.analyzed_at,
        },
    }