from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.app.models.bureau_report import BureauReport
from backend.app.models.loan_application import LoanApplication
from backend.app.schemas.bureau import BureauReportCreate


class BureauReportService:

    def create_report(
        self,
        db: Session,
        report: BureauReportCreate,
    ) -> BureauReport:

        application = db.get(
            LoanApplication,
            report.application_id,
        )

        if application is None:
            raise ValueError("APPLICATION_NOT_FOUND")

        bureau_report = BureauReport(
            bureau_report_id=f"BUREAU-{uuid4().hex[:12].upper()}",
            application_id=report.application_id,
            bureau_name=report.bureau_name,
            bureau_score=report.bureau_score,
            dpd=report.dpd,
            active_loans=report.active_loans,
            total_outstanding=report.total_outstanding,
            write_offs=report.write_offs,
            enquiries=report.enquiries,
            report_reference=report.report_reference,
            fetched_at=datetime.utcnow(),
        )

        db.add(bureau_report)
        db.commit()
        db.refresh(bureau_report)

        return bureau_report


bureau_report_service = BureauReportService()