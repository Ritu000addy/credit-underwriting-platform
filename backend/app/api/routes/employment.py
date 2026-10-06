from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.employment import (
    EmploymentCreate,
    EmploymentResponse,
)
from backend.app.schemas.common import ApiResponse
from backend.app.core.responses import success_response
from backend.app.services.employment_service import employment_service


router = APIRouter(
    prefix="/employment",
    tags=["Source Data Ingestion"],
)


@router.post(
    "",
    response_model=ApiResponse[EmploymentResponse],
)
def create_employment(
    employment: EmploymentCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    result = employment_service.create_employment(
        db=db,
        employment=employment,
    )

    response_data = EmploymentResponse.model_validate(result)

    return success_response(
        request=request,
        data=response_data,
        message="Employment / business data created successfully.",
    )