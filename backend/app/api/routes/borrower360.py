from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.borrower360 import Borrower360
from backend.app.services.borrower360_service import borrower360_service


router = APIRouter(
    prefix="/borrower-360",
    tags=["Borrower 360"],
)


@router.get(
    "/{customer_id}",
    response_model=Borrower360,
)
def get_borrower_360(
    customer_id: str,
    application_id: str | None = None,
    db: Session = Depends(get_db),
):
    try:
        return borrower360_service.build(
            db=db,
            customer_id=customer_id,
            application_id=application_id,
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