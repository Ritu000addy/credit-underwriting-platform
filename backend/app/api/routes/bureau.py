from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.bureau import (
    BureauReportCreate,
    BureauReportResponse,
)
from backend.app.schemas.common import ApiResponse
from backend.app.core.responses import success_response
from backend.app.services.bureau_report_service import bureau_report_service


router = APIRouter(
    prefix="/bureau-reports",
    tags=["Source Data Ingestion"],
)


@router.post(
    "",
    response_model=ApiResponse[BureauReportResponse],
)
def create_bureau_report(
    report: BureauReportCreate,
    request: Request,
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

    response_data = BureauReportResponse.model_validate(result)

    return success_response(
        request=request,
        data=response_data,
        message="Bureau report created successfully.",
    )