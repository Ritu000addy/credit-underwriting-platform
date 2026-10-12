from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db

from backend.app.core.workflow_logging import log_workflow_event
from backend.app.core.responses import success_response

from backend.app.models.customer import Customer

from backend.app.schemas.aadhaar_kyc import AadhaarKYCResponse
from backend.app.schemas.common import ApiResponse

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
    log_workflow_event(
        workflow="aadhaar_otp_send",
        event="started",
        request=request,
        entity_type="customer_aadhaar_kyc",
        entity_id=customer_id,
    )

    try:
        customer = db.get(Customer, customer_id)
    except Exception:
        log_workflow_event(
            workflow="aadhaar_otp_send",
            event="failed",
            request=request,
            entity_type="customer_aadhaar_kyc",
            entity_id=customer_id,
            error_code="CUSTOMER_LOOKUP_FAILED",
        )
        raise

    if customer is None:
        log_workflow_event(
            workflow="aadhaar_otp_send",
            event="failed",
            request=request,
            entity_type="customer_aadhaar_kyc",
            entity_id=customer_id,
            error_code="CUSTOMER_NOT_FOUND",
        )
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
        log_workflow_event(
            workflow="aadhaar_otp_send",
            event="failed",
            request=request,
            entity_type="customer_aadhaar_kyc",
            entity_id=customer_id,
            error_code="AADHAAR_OTP_REQUEST_REJECTED",
        )
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:
        log_workflow_event(
            workflow="aadhaar_otp_send",
            event="failed",
            request=request,
            entity_type="customer_aadhaar_kyc",
            entity_id=customer_id,
            error_code="AADHAAR_OTP_PROVIDER_FAILED",
        )
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )

    except Exception:
        log_workflow_event(
            workflow="aadhaar_otp_send",
            event="failed",
            request=request,
            entity_type="customer_aadhaar_kyc",
            entity_id=customer_id,
            error_code="AADHAAR_OTP_SEND_FAILED",
        )
        raise

    try:
        response_data = AadhaarKYCResponse.model_validate(result)
    except Exception:
        log_workflow_event(
            workflow="aadhaar_otp_send",
            event="failed",
            request=request,
            entity_type="customer_aadhaar_kyc",
            entity_id=customer_id,
            error_code="AADHAAR_OTP_RESPONSE_VALIDATION_FAILED",
        )
        raise

    log_workflow_event(
        workflow="aadhaar_otp_send",
        event="completed",
        request=request,
        entity_type="customer_aadhaar_kyc",
        entity_id=customer_id,
    )

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
    log_workflow_event(
        workflow="aadhaar_otp_verification",
        event="started",
        request=request,
        entity_type="customer_aadhaar_kyc",
        entity_id=customer_id,
    )

    try:
        customer = db.get(Customer, customer_id)
    except Exception:
        log_workflow_event(
            workflow="aadhaar_otp_verification",
            event="failed",
            request=request,
            entity_type="customer_aadhaar_kyc",
            entity_id=customer_id,
            error_code="CUSTOMER_LOOKUP_FAILED",
        )
        raise

    if customer is None:
        log_workflow_event(
            workflow="aadhaar_otp_verification",
            event="failed",
            request=request,
            entity_type="customer_aadhaar_kyc",
            entity_id=customer_id,
            error_code="CUSTOMER_NOT_FOUND",
        )
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
        log_workflow_event(
            workflow="aadhaar_otp_verification",
            event="failed",
            request=request,
            entity_type="customer_aadhaar_kyc",
            entity_id=customer_id,
            error_code="AADHAAR_OTP_VERIFICATION_REJECTED",
        )
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:
        log_workflow_event(
            workflow="aadhaar_otp_verification",
            event="failed",
            request=request,
            entity_type="customer_aadhaar_kyc",
            entity_id=customer_id,
            error_code="AADHAAR_OTP_PROVIDER_FAILED",
        )
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )

    except Exception:
        log_workflow_event(
            workflow="aadhaar_otp_verification",
            event="failed",
            request=request,
            entity_type="customer_aadhaar_kyc",
            entity_id=customer_id,
            error_code="AADHAAR_OTP_VERIFICATION_FAILED",
        )
        raise

    try:
        # Persist the Aadhaar KYC result
        customer.aadhaar_reference = result.masked_aadhaar
        customer.aadhaar_kyc_status = result.kyc_status

        db.commit()
        db.refresh(customer)

        response_data = AadhaarKYCResponse.model_validate(result)

    except Exception:
        db.rollback()
        log_workflow_event(
            workflow="aadhaar_otp_verification",
            event="failed",
            request=request,
            entity_type="customer_aadhaar_kyc",
            entity_id=customer_id,
            error_code="AADHAAR_KYC_PERSISTENCE_FAILED",
        )
        raise

    log_workflow_event(
        workflow="aadhaar_otp_verification",
        event="completed",
        request=request,
        entity_type="customer_aadhaar_kyc",
        entity_id=customer_id,
    )

    return success_response(
        request=request,
        data=response_data,
        message="Aadhaar KYC verified successfully.",
    )