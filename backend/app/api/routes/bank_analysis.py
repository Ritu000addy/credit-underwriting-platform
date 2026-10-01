from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.bank_analysis import BankAnalysisCreate
from backend.app.services.bank_analysis_service import bank_analysis_service


router = APIRouter(
    prefix="/bank-analysis",
    tags=["Source Data Ingestion"],
)


@router.post("")
def create_bank_analysis(
    analysis: BankAnalysisCreate,
    db: Session = Depends(get_db),
):
    try:
        result = bank_analysis_service.create_analysis(
            db=db,
            analysis=analysis,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    return {
        "message": "Bank analysis created successfully",
        "bank_analysis": {
            "bank_analysis_id": result.bank_analysis_id,
            "application_id": result.application_id,
            "monthly_credits": result.monthly_credits,
            "monthly_debits": result.monthly_debits,
            "average_balance": result.average_balance,
            "existing_emi": result.existing_emi,
            "bounce_count": result.bounce_count,
            "transactions_count": result.transactions_count,
            "income_trend": result.income_trend,
            "analysis_reference": result.analysis_reference,
            "analyzed_at": result.analyzed_at,
        },
    }