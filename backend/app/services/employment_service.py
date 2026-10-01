import uuid

from sqlalchemy.orm import Session

from backend.app.models.employment import Employment
from backend.app.schemas.employment import EmploymentCreate


class EmploymentService:

    def create_employment(
        self,
        db: Session,
        employment: EmploymentCreate,
    ):
        record = Employment(
            employment_id=f"EMP-{uuid.uuid4().hex[:12].upper()}",
            application_id=employment.application_id,
            employment_type=employment.employment_type,
            employer_name=employment.employer_name,
            monthly_income=employment.monthly_income,
            employment_vintage_months=employment.employment_vintage_months,
            business_name=employment.business_name,
            business_vintage_months=employment.business_vintage_months,
            gst_registered=employment.gst_registered,
            udyam_registered=employment.udyam_registered,
            income_source=employment.income_source,
            analysis_reference=employment.analysis_reference,
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return record


employment_service = EmploymentService()