from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Any

from backend.app.core.responses import success_response
from backend.app.database import get_db
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.operations import (
    OperationsDashboardResponse,
    OperationsApplicationListResponse,
    OperationsApplicationResponse,
    OperationsManualReviewResponse,
    OperationsExceptionResponse,
    OperationsDisbursementResponse,
    OperationsReconciliationResponse,
    OperationsOverdueCollectionResponse,
)
from backend.app.services.operations_service import (
    operations_service,
)
from backend.app.services.reconciliation_service import (
    reconciliation_service,
)


router = APIRouter(
    prefix="/operations",
    tags=["Credit Operations"],
)

@router.post(
    "/queue",
    response_model=ApiResponse[dict[str, Any]],
)
def update_operations_queue_status(
    queue_id: str,
    queue_status: str,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        result = reconciliation_service.update_operations_queue_status(
            db=db,
            queue_id=queue_id,
            queue_status=queue_status,
        )

    except ValueError as exc:
        if str(exc) == "OPERATIONS_QUEUE_NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail="Operations queue item not found",
            )

        if str(exc) == "INVALID_OPERATIONS_QUEUE_STATUS":
            raise HTTPException(
                status_code=400,
                detail="Invalid operations queue status",
            )

        if str(exc) == "OPERATIONS_QUEUE_ALREADY_RESOLVED":
            raise HTTPException(
                status_code=400,
                detail="Operations queue item is already resolved",
            )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    response_data = {
        "queue_id": result.queue_id,
        "reconciliation_id": result.reconciliation_id,
        "disbursement_id": result.disbursement_id,
        "queue_type": result.queue_type,
        "queue_status": result.queue_status,
        "reason": result.reason,
    }

    return success_response(
        request=request,
        data=response_data,
        message="Operations queue status updated successfully.",
    )

@router.get(
    "/dashboard",
    response_model=ApiResponse[OperationsDashboardResponse],
)
def get_operations_dashboard(
    request: Request,
    db: Session = Depends(get_db),
):
    result = operations_service.get_dashboard(db)

    return success_response(
        request=request,
        data=result,
        message="Operations dashboard retrieved successfully.",
    )


@router.get(
    "/applications",
    response_model=ApiResponse[OperationsApplicationListResponse],
)
def list_operations_applications(
    request: Request,
    application_id: str | None = None,
    customer_id: str | None = None,
    status: str | None = None,
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
):
    result = operations_service.list_applications(
        db=db,
        application_id=application_id,
        customer_id=customer_id,
        status=status,
        limit=limit,
        offset=offset,
    )

    return success_response(
        request=request,
        data=result,
        message="Operations applications retrieved successfully.",
    )


@router.get(
    "/applications/{application_id}",
    response_model=ApiResponse[OperationsApplicationResponse],
)
def get_operations_application(
    application_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    result = operations_service.get_application(
        db=db,
        application_id=application_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="APPLICATION_NOT_FOUND",
        )

    return success_response(
        request=request,
        data=result,
        message="Operations application retrieved successfully.",
    )


@router.get(
    "/manual-review",
    response_model=ApiResponse[list[OperationsManualReviewResponse]],
)
def list_operations_manual_reviews(
    request: Request,
    review_status: str | None = None,
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
):
    result = operations_service.list_manual_reviews(
        db=db,
        review_status=review_status,
        limit=limit,
        offset=offset,
    )

    return success_response(
        request=request,
        data=result,
        message="Operations manual reviews retrieved successfully.",
    )


@router.get(
    "/exceptions",
    response_model=ApiResponse[list[OperationsExceptionResponse]],
)
def list_operations_exceptions(
    request: Request,
    status: str | None = None,
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
):
    result = operations_service.list_exceptions(
        db=db,
        status=status,
        limit=limit,
        offset=offset,
    )

    return success_response(
        request=request,
        data=result,
        message="Operations exceptions retrieved successfully.",
    )


@router.get(
    "/disbursements",
    response_model=ApiResponse[list[OperationsDisbursementResponse]],
)
def list_operations_disbursements(
    request: Request,
    status: str | None = None,
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
):
    result = operations_service.list_disbursements(
        db=db,
        status=status,
        limit=limit,
        offset=offset,
    )

    return success_response(
        request=request,
        data=result,
        message="Operations disbursements retrieved successfully.",
    )


@router.get(
    "/reconciliation",
    response_model=ApiResponse[list[OperationsReconciliationResponse]],
)
def list_operations_reconciliation(
    request: Request,
    status: str | None = None,
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
):
    result = operations_service.list_reconciliation(
        db=db,
        status=status,
        limit=limit,
        offset=offset,
    )

    return success_response(
        request=request,
        data=result,
        message="Operations reconciliation records retrieved successfully.",
    )


@router.get(
    "/collections/overdue",
    response_model=ApiResponse[list[OperationsOverdueCollectionResponse]],
)
def list_operations_overdue_collections(
    request: Request,
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
):
    result = operations_service.list_overdue_collections(
        db=db,
        limit=limit,
        offset=offset,
    )

    return success_response(
        request=request,
        data=result,
        message="Operations overdue collections retrieved successfully.",
    )