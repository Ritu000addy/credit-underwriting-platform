import uuid

from sqlalchemy.orm import Session

from backend.app.models.manual_review import ManualReview


class ManualReviewService:

    def create_review(
        self,
        db: Session,
        application_id: str,
        review_reason: str | None = None,
    ) -> ManualReview:

        existing_review = (
            db.query(ManualReview)
            .filter(
                ManualReview.application_id == application_id,
                ManualReview.review_status == "OPEN",
            )
            .first()
        )

        if existing_review is not None:
            return existing_review

        review = ManualReview(
            review_id=f"REV-{uuid.uuid4().hex[:12].upper()}",
            application_id=application_id,
            review_status="OPEN",
            review_reason=review_reason,
        )

        db.add(review)
        db.commit()
        db.refresh(review)

        return review

    def get_review(
        self,
        db: Session,
        application_id: str,
    ) -> ManualReview | None:

        return (
            db.query(ManualReview)
            .filter(
                ManualReview.application_id == application_id,
            )
            .order_by(ManualReview.created_at.desc())
            .first()
        )


manual_review_service = ManualReviewService()