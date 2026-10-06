from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.core.responses import success_response
from backend.app.database import get_db
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.underwriting_validation import (
    UnderwritingValidationResponse,
)
from backend.app.services.borrower360_service import borrower360_service
from backend.app.services.underwriting_validation_service import (
    underwriting_validation_service,
)


router = APIRouter(
    prefix="/underwriting",
    tags=["AI Credit Underwriting"],
)


@router.get(
    "/{customer_id}/validation",
    response_model=ApiResponse[UnderwritingValidationResponse],
)
def validate_underwriting_input(
    customer_id: str,
    application_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        borrower = borrower360_service.build(
            db=db,
            customer_id=customer_id,
            application_id=application_id,
        )

        result = underwriting_validation_service.validate(
            borrower=borrower,
        )

        result.application_id = application_id

        response_data = UnderwritingValidationResponse.model_validate(result)

        return success_response(
            request=request,
            data=response_data,
            message="Underwriting input validation completed successfully.",
        )

    except ValueError as exc:

        if str(exc) == "CUSTOMER_NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail="CUSTOMER_NOT_FOUND",
            )

        if str(exc) == "APPLICATION_NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail="APPLICATION_NOT_FOUND",
            )

        if str(exc) == "APPLICATION_CUSTOMER_MISMATCH":
            raise HTTPException(
                status_code=400,
                detail="APPLICATION_CUSTOMER_MISMATCH",
            )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )