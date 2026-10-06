from fastapi import APIRouter, HTTPException, Request

from backend.app.core.responses import success_response
from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.common import ApiResponse
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
    response_model=ApiResponse[GenAIUnderwritingResult],
)
def analyze_underwriting(
    borrower: Borrower360,
    underwriting: UnderwritingResult,
    request: Request,
):
    if borrower.customer_id != underwriting.customer_id:
        raise HTTPException(
            status_code=400,
            detail="Borrower and underwriting customer IDs do not match.",
        )

    if borrower.customer_id and underwriting.application_id:
        try:
            result = genai_underwriting_service.generate(
                borrower=borrower,
                underwriting=underwriting,
            )

            response_data = GenAIUnderwritingResult.model_validate(result)

            return success_response(
                request=request,
                data=response_data,
                message="GenAI underwriting analysis completed successfully.",
            )

        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail=str(exc),
            )

    raise HTTPException(
        status_code=400,
        detail="Borrower and underwriting data are required.",
    )