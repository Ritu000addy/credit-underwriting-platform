from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
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


router = APIRouter(
    prefix="/operations",
    tags=["Credit Operations"],
)


@router.get(
    "/dashboard",
    response_model=OperationsDashboardResponse,
)
def get_operations_dashboard(
    db: Session = Depends(get_db),
):
    return operations_service.get_dashboard(db)


@router.get(
    "/applications",
    response_model=OperationsApplicationListResponse,
)
def list_operations_applications(
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
    return operations_service.list_applications(
        db=db,
        application_id=application_id,
        customer_id=customer_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/applications/{application_id}",
    response_model=OperationsApplicationResponse,
)
def get_operations_application(
    application_id: str,
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

    return result


@router.get(
    "/manual-review",
    response_model=list[OperationsManualReviewResponse],
)
def list_operations_manual_reviews(
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
    return operations_service.list_manual_reviews(
        db=db,
        review_status=review_status,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/exceptions",
    response_model=list[OperationsExceptionResponse],
)
def list_operations_exceptions(
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
    return operations_service.list_exceptions(
        db=db,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/disbursements",
    response_model=list[OperationsDisbursementResponse],
)
def list_operations_disbursements(
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
    return operations_service.list_disbursements(
        db=db,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/reconciliation",
    response_model=list[OperationsReconciliationResponse],
)
def list_operations_reconciliation(
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
    return operations_service.list_reconciliation(
        db=db,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/collections/overdue",
    response_model=list[OperationsOverdueCollectionResponse],
)
def list_operations_overdue_collections(
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
    return operations_service.list_overdue_collections(
        db=db,
        limit=limit,
        offset=offset,
    )