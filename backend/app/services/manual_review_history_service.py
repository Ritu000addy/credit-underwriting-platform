import uuid

from sqlalchemy.orm import Session

from backend.app.models.manual_review_history import ManualReviewHistory


class ManualReviewHistoryService:

    def record(
        self,
        db: Session,
        review_id: str,
        application_id: str,
        action: str,
        previous_status: str | None,
        new_status: str | None,
        actor_type: str,
        actor_reference: str | None = None,
        reviewer_id: str | None = None,
        reviewer_decision: str | None = None,
        remarks: str | None = None,
    ) -> ManualReviewHistory:

        history = ManualReviewHistory(
            history_id=f"MRH-{uuid.uuid4().hex[:12].upper()}",
            review_id=review_id,
            application_id=application_id,
            action=action,
            previous_status=previous_status,
            new_status=new_status,
            actor_type=actor_type,
            actor_reference=actor_reference,
            reviewer_id=reviewer_id,
            reviewer_decision=reviewer_decision,
            remarks=remarks,
        )

        db.add(history)
        db.flush()

        return history

    def get_by_review(
        self,
        db: Session,
        review_id: str,
    ) -> list[ManualReviewHistory]:

        return (
            db.query(ManualReviewHistory)
            .filter(
                ManualReviewHistory.review_id == review_id
            )
            .order_by(ManualReviewHistory.created_at.asc())
            .all()
        )

    def get_by_application(
        self,
        db: Session,
        application_id: str,
    ) -> list[ManualReviewHistory]:

        return (
            db.query(ManualReviewHistory)
            .filter(
                ManualReviewHistory.application_id == application_id
            )
            .order_by(ManualReviewHistory.created_at.asc())
            .all()
        )


manual_review_history_service = ManualReviewHistoryService()