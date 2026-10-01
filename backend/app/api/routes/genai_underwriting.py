from fastapi import APIRouter, HTTPException

from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.underwriting import UnderwritingResult
from backend.app.schemas.genai_underwriting import GenAIUnderwritingResult
from backend.app.services.genai_underwriting_service import (
    genai_underwriting_service,
)


router = APIRouter(
    prefix="/genai-underwriting",
    tags=["GenAI Underwriting"],
)


@router.post(
    "/analyze",
    response_model=GenAIUnderwritingResult,
)
def analyze_underwriting(
    borrower: Borrower360,
    underwriting: UnderwritingResult,
):

    if borrower.customer_id != underwriting.customer_id:
        raise HTTPException(
            status_code=400,
            detail="Borrower and underwriting customer IDs do not match.",
        )

    if borrower.customer_id and underwriting.application_id:
        result = genai_underwriting_service.generate(
            borrower=borrower,
            underwriting=underwriting,
        )

        return result

    raise HTTPException(
        status_code=400,
        detail="Borrower and underwriting data are required.",
    )