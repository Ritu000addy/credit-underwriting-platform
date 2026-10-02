from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db

from backend.app.schemas.application import ApplicationCreate
from backend.app.services.application_service import application_service

router = APIRouter(
    prefix="/applications",
    tags=["LOS Origination"],
)

@router.post("")
def create_application(
    application: ApplicationCreate,
    db: Session = Depends(get_db),
):
    result = application_service.create_application(
        db=db,
        application=application,
    )

    return {
        "message": "Application created successfully",
        "application": {
            "application_id": result.application_id,
            "customer_id": result.customer_id,
            "requested_amount": result.requested_amount,
            "status": result.status,
        },
    }


@router.get("/{application_id}")
def get_application(
    application_id: str,
    db: Session = Depends(get_db),
):
    result = application_service.get_application(
        db=db,
        application_id=application_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return {
        "application_id": result.application_id,
        "customer_id": result.customer_id,
        "product": result.product,
        "requested_amount": result.requested_amount,
        "status": result.status,
        "created_at": result.created_at,
        "updated_at": result.updated_at,
    }