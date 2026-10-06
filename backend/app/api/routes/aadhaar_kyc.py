from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.customer import Customer
from backend.app.schemas.aadhaar_kyc import AadhaarKYCResponse
from backend.app.schemas.common import ApiResponse
from backend.app.core.responses import success_response
from backend.app.services.aadhaar_kyc_service import aadhaar_kyc_service


router = APIRouter(
    prefix="/kyc/aadhaar",
    tags=["Source Data Ingestion"],
)


@router.post(
    "/send-otp",
    response_model=ApiResponse[AadhaarKYCResponse],
)
def send_aadhaar_otp(
    customer_id: str,
    aadhaar_number: str,
    user_consent: bool,
    request: Request,
    user_id: str | None = None,
    workflow_session_token: str | None = None,
    db: Session = Depends(get_db),
):
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        )

    try:
        result = aadhaar_kyc_service.send_otp(
            aadhaar_number=aadhaar_number,
            user_consent=user_consent,
            user_id=user_id,
            workflow_session_token=workflow_session_token,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )

    response_data = AadhaarKYCResponse.model_validate(result)

    return success_response(
        request=request,
        data=response_data,
        message="Aadhaar OTP sent successfully.",
    )


@router.post(
    "/verify-otp",
    response_model=ApiResponse[AadhaarKYCResponse],
)
def verify_aadhaar_otp(
    customer_id: str,
    session_id: str,
    otp: str,
    request: Request,
    user_id: str | None = None,
    workflow_session_token: str | None = None,
    db: Session = Depends(get_db),
):
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        )

    try:
        result = aadhaar_kyc_service.verify_otp(
            session_id=session_id,
            otp=otp,
            user_id=user_id,
            workflow_session_token=workflow_session_token,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )

    # Persist the Aadhaar KYC result
    customer.aadhaar_reference = result.masked_aadhaar
    customer.aadhaar_kyc_status = result.kyc_status

    db.commit()
    db.refresh(customer)

    response_data = AadhaarKYCResponse.model_validate(result)

    return success_response(
        request=request,
        data=response_data,
        message="Aadhaar KYC verified successfully.",
    )