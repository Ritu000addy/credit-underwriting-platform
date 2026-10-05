import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db

from backend.app.schemas.review_exception import (
    ReviewExceptionAssign,
    ReviewExceptionClose,
    ReviewExceptionCreate,
    ReviewExceptionInformationRequest,
    ReviewExceptionResolve,
    ReviewExceptionResponse,
    ReviewExceptionResumeInformation,
)

from backend.app.services.audit_log_service import audit_log_service
from backend.app.services.review_exception_service import (
    review_exception_service,
)


router = APIRouter(
    prefix="/review-exceptions",
    tags=["Review Exceptions"],
)


@router.post(
    "",
    response_model=ReviewExceptionResponse,
)
def create_review_exception(
    request: ReviewExceptionCreate,
    db: Session = Depends(get_db),
):
    try:
        result = review_exception_service.create_exception(
            db=db,
            review_id=request.review_id,
            application_id=request.application_id,
            exception_type=request.exception_type,
            description=request.description,
            created_by=request.created_by,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=result.application_id,
            actor_type="USER" if request.created_by else "SYSTEM",
            actor_reference=request.created_by,
            action="REVIEW_EXCEPTION_CREATED",
            entity_type="REVIEW_EXCEPTION",
            entity_reference=result.exception_id,
            description="Review exception created.",
            previous_state=None,
            new_state="OPEN",
            request_reference=result.application_id,
        )

        db.commit()
        db.refresh(result)

        return result

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="REVIEW_EXCEPTION_CREATION_FAILED",
        )


@router.get(
    "/{exception_id}",
    response_model=ReviewExceptionResponse,
)
def get_review_exception(
    exception_id: str,
    db: Session = Depends(get_db),
):
    result = review_exception_service.get_exception(
        db=db,
        exception_id=exception_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Review exception not found.",
        )

    return result


@router.get(
    "/application/{application_id}",
    response_model=list[ReviewExceptionResponse],
)
def get_application_exceptions(
    application_id: str,
    db: Session = Depends(get_db),
):
    return review_exception_service.get_by_application(
        db=db,
        application_id=application_id,
    )


@router.post(
    "/{exception_id}/assign",
    response_model=ReviewExceptionResponse,
)
def assign_review_exception(
    exception_id: str,
    request: ReviewExceptionAssign,
    db: Session = Depends(get_db),
):
    exception = review_exception_service.get_exception(
        db=db,
        exception_id=exception_id,
    )

    if exception is None:
        raise HTTPException(
            status_code=404,
            detail="Review exception not found.",
        )

    try:
        previous_status = exception.status

        result = review_exception_service.assign_exception(
            db=db,
            exception=exception,
            assigned_to=request.assigned_to,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=result.application_id,
            actor_type="USER",
            actor_reference=request.assigned_to,
            action="REVIEW_EXCEPTION_ASSIGNED",
            entity_type="REVIEW_EXCEPTION",
            entity_reference=result.exception_id,
            description=(
                f"Review exception assigned to "
                f"{request.assigned_to}."
            ),
            previous_state=previous_status,
            new_state=result.status,
            request_reference=result.application_id,
        )

        db.commit()
        db.refresh(result)

        return result

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="REVIEW_EXCEPTION_ASSIGNMENT_FAILED",
        )


@router.post(
    "/{exception_id}/request-information",
    response_model=ReviewExceptionResponse,
)
def request_exception_information(
    exception_id: str,
    request: ReviewExceptionInformationRequest,
    db: Session = Depends(get_db),
):
    exception = review_exception_service.get_exception(
        db=db,
        exception_id=exception_id,
    )

    if exception is None:
        raise HTTPException(
            status_code=404,
            detail="Review exception not found.",
        )

    try:
        previous_status = exception.status

        result = review_exception_service.request_information(
            db=db,
            exception=exception,
            requested_information=request.requested_information,
            actor_id=request.actor_id,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=result.application_id,
            actor_type="USER",
            actor_reference=request.actor_id,
            action="REVIEW_EXCEPTION_INFORMATION_REQUESTED",
            entity_type="REVIEW_EXCEPTION",
            entity_reference=result.exception_id,
            description=(
                "Additional information requested for "
                "review exception."
            ),
            previous_state=previous_status,
            new_state=result.status,
            request_reference=result.application_id,
        )

        db.commit()
        db.refresh(result)

        return result

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="REVIEW_EXCEPTION_INFORMATION_REQUEST_FAILED",
        )


@router.post(
    "/{exception_id}/resume",
    response_model=ReviewExceptionResponse,
)
def resume_review_exception(
    exception_id: str,
    request: ReviewExceptionResumeInformation,
    db: Session = Depends(get_db),
):
    exception = review_exception_service.get_exception(
        db=db,
        exception_id=exception_id,
    )

    if exception is None:
        raise HTTPException(
            status_code=404,
            detail="Review exception not found.",
        )

    try:
        previous_status = exception.status

        result = review_exception_service.resume_from_information(
            db=db,
            exception=exception,
            actor_id=request.actor_id,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=result.application_id,
            actor_type="USER",
            actor_reference=request.actor_id,
            action="REVIEW_EXCEPTION_RESUMED",
            entity_type="REVIEW_EXCEPTION",
            entity_reference=result.exception_id,
            description=(
                "Review exception resumed after "
                "information was received."
            ),
            previous_state=previous_status,
            new_state=result.status,
            request_reference=result.application_id,
        )

        db.commit()
        db.refresh(result)

        return result

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="REVIEW_EXCEPTION_RESUME_FAILED",
        )


@router.post(
    "/{exception_id}/resolve",
    response_model=ReviewExceptionResponse,
)
def resolve_review_exception(
    exception_id: str,
    request: ReviewExceptionResolve,
    db: Session = Depends(get_db),
):
    exception = review_exception_service.get_exception(
        db=db,
        exception_id=exception_id,
    )

    if exception is None:
        raise HTTPException(
            status_code=404,
            detail="Review exception not found.",
        )

    try:
        previous_status = exception.status

        result = review_exception_service.resolve_exception(
            db=db,
            exception=exception,
            resolution_action=request.resolution_action,
            resolution_remarks=request.resolution_remarks,
            resolved_by=request.resolved_by,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=result.application_id,
            actor_type="USER",
            actor_reference=request.resolved_by,
            action="REVIEW_EXCEPTION_RESOLVED",
            entity_type="REVIEW_EXCEPTION",
            entity_reference=result.exception_id,
            description=(
                f"Review exception resolved with action "
                f"{request.resolution_action}."
            ),
            previous_state=previous_status,
            new_state=result.status,
            request_reference=result.application_id,
        )

        db.commit()
        db.refresh(result)

        return result

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="REVIEW_EXCEPTION_RESOLUTION_FAILED",
        )


@router.post(
    "/{exception_id}/close",
    response_model=ReviewExceptionResponse,
)
def close_review_exception(
    exception_id: str,
    request: ReviewExceptionClose,
    db: Session = Depends(get_db),
):
    exception = review_exception_service.get_exception(
        db=db,
        exception_id=exception_id,
    )

    if exception is None:
        raise HTTPException(
            status_code=404,
            detail="Review exception not found.",
        )

    try:
        previous_status = exception.status

        result = review_exception_service.close_exception(
            db=db,
            exception=exception,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=result.application_id,
            actor_type="USER",
            actor_reference=request.actor_id,
            action="REVIEW_EXCEPTION_CLOSED",
            entity_type="REVIEW_EXCEPTION",
            entity_reference=result.exception_id,
            description="Review exception closed.",
            previous_state=previous_status,
            new_state=result.status,
            request_reference=result.application_id,
        )

        db.commit()
        db.refresh(result)

        return result

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="REVIEW_EXCEPTION_CLOSURE_FAILED",
        )