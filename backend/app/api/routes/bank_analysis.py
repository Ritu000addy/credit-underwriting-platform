from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.bank_analysis import (
    BankAnalysisCreate,
    BankAnalysisResponse,
)
from backend.app.schemas.common import ApiResponse
from backend.app.core.responses import success_response
from backend.app.services.bank_analysis_service import bank_analysis_service


router = APIRouter(
    prefix="/bank-analysis",
    tags=["Source Data Ingestion"],
)


@router.post(
    "",
    response_model=ApiResponse[BankAnalysisResponse],
)
def create_bank_analysis(
    analysis: BankAnalysisCreate,
    request: Request,
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

    response_data = BankAnalysisResponse.model_validate(result)

    return success_response(
        request=request,
        data=response_data,
        message="Bank analysis created successfully.",
    )