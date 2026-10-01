from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.bureau import BureauReportCreate
from backend.app.services.bureau_report_service import bureau_report_service


router = APIRouter(
    prefix="/bureau-reports",
    tags=["Source Data Ingestion"],
)


@router.post("")
def create_bureau_report(
    report: BureauReportCreate,
    db: Session = Depends(get_db),
):
    try:
        result = bureau_report_service.create_report(
            db=db,
            report=report,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    return {
        "message": "Bureau report created successfully",
        "bureau_report": {
            "bureau_report_id": result.bureau_report_id,
            "application_id": result.application_id,
            "bureau_name": result.bureau_name,
            "bureau_score": result.bureau_score,
            "dpd": result.dpd,
            "active_loans": result.active_loans,
            "total_outstanding": result.total_outstanding,
            "write_offs": result.write_offs,
            "enquiries": result.enquiries,
            "report_reference": result.report_reference,
            "fetched_at": result.fetched_at,
        },
    }