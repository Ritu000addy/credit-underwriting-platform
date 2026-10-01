from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.customer import (
    CustomerCreate,
    CustomerResponse,
)
from backend.app.services.customer_service import customer_service


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.post(
    "",
    response_model=CustomerResponse,
)
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
):
    try:
        result = customer_service.create_customer(
            db=db,
            customer_id=customer.customer_id,
            kyc_status=customer.kyc_status,
            pan=customer.pan,
            aadhaar_reference=customer.aadhaar_reference,
            aadhaar_kyc_status=customer.aadhaar_kyc_status,
            dob=customer.dob,
            address=customer.address,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    return result