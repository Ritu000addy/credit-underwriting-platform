from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.internal_history import (
    InternalHistoryCreate,
    InternalHistoryResponse,
)
from backend.app.schemas.common import ApiResponse
from backend.app.core.responses import success_response
from backend.app.services.internal_history_service import (
    internal_history_service,
)


router = APIRouter(
    prefix="/internal-history",
    tags=["Source Data Ingestion"],
)


@router.post(
    "",
    response_model=ApiResponse[InternalHistoryResponse],
)
def create_internal_history(
    history: InternalHistoryCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    result = internal_history_service.create_internal_history(
        db=db,
        history=history,
    )

    response_data = InternalHistoryResponse.model_validate(result)

    return success_response(
        request=request,
        data=response_data,
        message="Internal loan history created successfully.",
    )