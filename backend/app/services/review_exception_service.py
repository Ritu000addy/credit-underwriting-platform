import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.models.review_exception import ReviewException


class ReviewExceptionService:

    def create_exception(
        self,
        db: Session,
        review_id: str,
        application_id: str,
        exception_type: str,
        description: str,
        created_by: str | None = None,
    ) -> ReviewException:

        exception = ReviewException(
            exception_id=f"EXC-{uuid.uuid4().hex[:12].upper()}",
            review_id=review_id,
            application_id=application_id,
            exception_type=exception_type.strip(),
            description=description.strip(),
            status="OPEN",
            created_by=created_by,
        )

        db.add(exception)
        db.flush()

        return exception

    def assign_exception(
        self,
        db: Session,
        exception: ReviewException,
        assigned_to: str,
    ) -> ReviewException:

        if exception.status not in {"OPEN", "IN_PROGRESS"}:
            raise ValueError(
                "EXCEPTION_NOT_ELIGIBLE_FOR_ASSIGNMENT"
            )

        assigned_to = assigned_to.strip()

        if not assigned_to:
            raise ValueError("ASSIGNED_TO_REQUIRED")

        if len(assigned_to) > 100:
            raise ValueError("ASSIGNED_TO_TOO_LONG")

        exception.assigned_to = assigned_to
        exception.status = "IN_PROGRESS"

        db.flush()

        return exception

    def request_information(
        self,
        db: Session,
        exception: ReviewException,
        requested_information: str,
        actor_id: str,
    ) -> ReviewException:

        if exception.status != "IN_PROGRESS":
            raise ValueError(
                "EXCEPTION_NOT_ELIGIBLE_FOR_INFORMATION_REQUEST"
            )

        requested_information = requested_information.strip()
        actor_id = actor_id.strip()

        if not requested_information:
            raise ValueError("REQUESTED_INFORMATION_REQUIRED")

        if not actor_id:
            raise ValueError("ACTOR_ID_REQUIRED")

        if len(actor_id) > 100:
            raise ValueError("ACTOR_ID_TOO_LONG")

        exception.requested_information = requested_information
        exception.resolution_action = "REQUEST_INFORMATION"
        exception.resolved_by = None
        exception.resolved_at = None
        exception.status = "WAITING_FOR_INFORMATION"

        db.flush()

        return exception

    def resume_from_information(
        self,
        db: Session,
        exception: ReviewException,
        actor_id: str,
    ) -> ReviewException:

        if exception.status != "WAITING_FOR_INFORMATION":
            raise ValueError(
                "EXCEPTION_NOT_WAITING_FOR_INFORMATION"
            )

        actor_id = actor_id.strip()

        if not actor_id:
            raise ValueError("ACTOR_ID_REQUIRED")

        if len(actor_id) > 100:
            raise ValueError("ACTOR_ID_TOO_LONG")

        exception.status = "IN_PROGRESS"
        exception.resolution_action = None
        exception.resolved_by = None
        exception.resolved_at = None

        db.flush()

        return exception

    def resolve_exception(
        self,
        db: Session,
        exception: ReviewException,
        resolution_action: str,
        resolution_remarks: str | None,
        resolved_by: str,
    ) -> ReviewException:

        if exception.status != "IN_PROGRESS":
            raise ValueError(
                "EXCEPTION_NOT_ELIGIBLE_FOR_RESOLUTION"
            )

        resolution_action = resolution_action.strip().upper()
        resolved_by = resolved_by.strip()

        if resolution_action not in {"APPROVE", "REJECT"}:
            raise ValueError(
                "INVALID_EXCEPTION_RESOLUTION_ACTION"
            )

        if not resolved_by:
            raise ValueError("RESOLVED_BY_REQUIRED")

        if len(resolved_by) > 100:
            raise ValueError("RESOLVED_BY_TOO_LONG")

        if resolution_remarks is not None:
            resolution_remarks = resolution_remarks.strip() or None

        exception.resolution_action = resolution_action
        exception.resolution_remarks = resolution_remarks
        exception.resolved_by = resolved_by
        exception.resolved_at = datetime.utcnow()
        exception.status = "RESOLVED"

        db.flush()

        return exception

    def close_exception(
        self,
        db: Session,
        exception: ReviewException,
    ) -> ReviewException:

        if exception.status != "RESOLVED":
            raise ValueError(
                "EXCEPTION_NOT_ELIGIBLE_FOR_CLOSURE"
            )

        exception.status = "CLOSED"

        db.flush()

        return exception

    def get_exception(
        self,
        db: Session,
        exception_id: str,
    ) -> ReviewException | None:

        return (
            db.query(ReviewException)
            .filter(
                ReviewException.exception_id == exception_id
            )
            .first()
        )

    def get_by_review(
        self,
        db: Session,
        review_id: str,
    ) -> list[ReviewException]:

        return (
            db.query(ReviewException)
            .filter(
                ReviewException.review_id == review_id
            )
            .order_by(ReviewException.created_at.asc())
            .all()
        )

    def get_by_application(
        self,
        db: Session,
        application_id: str,
    ) -> list[ReviewException]:

        return (
            db.query(ReviewException)
            .filter(
                ReviewException.application_id == application_id
            )
            .order_by(ReviewException.created_at.asc())
            .all()
        )


review_exception_service = ReviewExceptionService()