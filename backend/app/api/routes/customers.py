from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db

from backend.app.core.responses import success_response
from backend.app.core.workflow_logging import log_workflow_event

from backend.app.schemas.customer import (
    CustomerCreate,
    CustomerResponse,
)

from backend.app.schemas.common import ApiResponse

from backend.app.services.customer_service import customer_service


router = APIRouter(
    prefix="/customers",
    tags=["LOS Origination"],
)


@router.post(
    "",
    response_model=ApiResponse[CustomerResponse],
)
def create_customer(
    customer: CustomerCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    customer_id = customer.customer_id

    log_workflow_event(
        workflow="customer_creation",
        event="started",
        request=request,
        entity_type="customer",
        entity_id=customer_id,
    )
    
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
        log_workflow_event(
            workflow="customer_creation",
            event="failed",
            request=request,
            entity_type="customer",
            entity_id=customer_id,
            error_code="CUSTOMER_CREATION_REJECTED",
        )
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        log_workflow_event(
            workflow="customer_creation",
            event="failed",
            request=request,
            entity_type="customer",
            entity_id=customer_id,
            error_code="CUSTOMER_CREATION_FAILED",
        )
        raise

    try:
        response_data = CustomerResponse.model_validate(result)

    except Exception:
        log_workflow_event(
            workflow="customer_creation",
            event="failed",
            request=request,
            entity_type="customer",
            entity_id=customer_id,
            error_code="CUSTOMER_RESPONSE_VALIDATION_FAILED",
        )
        raise

    log_workflow_event(
        workflow="customer_creation",
        event="completed",
        request=request,
        entity_type="customer",
        entity_id=customer_id,
    )

    return success_response(
        request=request,
        data=response_data,
        message="Customer created successfully.",
    )