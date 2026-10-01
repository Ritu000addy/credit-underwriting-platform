from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services.borrower360_service import borrower360_service
from backend.app.services.policy_validation_service import (
    policy_validation_service,
)
from backend.app.schemas.policy_validation import (
    PolicyValidationResponse,
)


router = APIRouter(
    prefix="/underwriting",
    tags=["AI Credit Underwriting"],
)


@router.get(
    "/{customer_id}/policy-validation",
    response_model=PolicyValidationResponse,
)
def validate_policy(
    customer_id: str,
    application_id: str,
    db: Session = Depends(get_db),
):
    try:
        borrower = borrower360_service.build(
            db=db,
            customer_id=customer_id,
            application_id=application_id,
        )

        result = policy_validation_service.validate(
            borrower=borrower,
            application_id=application_id,
        )

        return result

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