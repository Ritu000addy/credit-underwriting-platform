from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.employment import EmploymentCreate
from backend.app.services.employment_service import employment_service


router = APIRouter(
    prefix="/employment",
    tags=["Source Data Ingestion"],
)


@router.post("")
def create_employment(
    employment: EmploymentCreate,
    db: Session = Depends(get_db),
):
    result = employment_service.create_employment(
        db=db,
        employment=employment,
    )

    return {
        "message": "Employment / business data created successfully",
        "employment": {
            "employment_id": result.employment_id,
            "application_id": result.application_id,
            "employment_type": result.employment_type,
            "employer_name": result.employer_name,
            "monthly_income": result.monthly_income,
            "employment_vintage_months": result.employment_vintage_months,
            "business_name": result.business_name,
            "business_vintage_months": result.business_vintage_months,
            "gst_registered": result.gst_registered,
            "udyam_registered": result.udyam_registered,
            "income_source": result.income_source,
            "analysis_reference": result.analysis_reference,
            "analyzed_at": result.analyzed_at,
        },
    }