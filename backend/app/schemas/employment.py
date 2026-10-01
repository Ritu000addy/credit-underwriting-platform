from pydantic import BaseModel
from typing import Optional


class EmploymentCreate(BaseModel):
    application_id: str

    employment_type: Optional[str] = None
    employer_name: Optional[str] = None
    monthly_income: Optional[float] = None
    employment_vintage_months: Optional[int] = None

    business_name: Optional[str] = None
    business_vintage_months: Optional[int] = None
    gst_registered: Optional[bool] = None
    udyam_registered: Optional[bool] = None

    income_source: Optional[str] = None
    analysis_reference: Optional[str] = None