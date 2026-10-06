import uuid

from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.models.manual_review import ManualReview
from backend.app.models.credit_decision import CreditDecision
from backend.app.models.loan_application import LoanApplication

class ManualReviewService:

    def create_review(
        self,
        db: Session,
        application_id: str,
        review_reason: str | None = None,
    ) -> ManualReview:

        application_id = application_id.strip()

        if not application_id:
            raise ValueError("APPLICATION_ID_REQUIRED")

        if len(application_id) > 50:
            raise ValueError("APPLICATION_ID_TOO_LONG")

        if review_reason is not None:
            review_reason = review_reason.strip()

            if not review_reason:
                raise ValueError("MANUAL_REVIEW_REASON_REQUIRED")

            if len(review_reason) > 1000:
                raise ValueError("MANUAL_REVIEW_REASON_TOO_LONG")

        application = db.get(
            LoanApplication,
            application_id,
        )

        if application is None:
            raise ValueError("APPLICATION_NOT_FOUND")

        if application.status not in {
            "SUBMITTED",
            "UNDERWRITING_COMPLETED",
            "REFERRED",
        }:
            raise ValueError("APPLICATION_NOT_ELIGIBLE_FOR_MANUAL_REVIEW")

        credit_decision = (
            db.query(CreditDecision)
            .filter(
                CreditDecision.application_id == application_id,
            )
            .order_by(CreditDecision.created_at.desc())
            .first()
        )

        if credit_decision is None:
            raise ValueError("CREDIT_DECISION_NOT_FOUND")

        if credit_decision.decision != "REFER":
            raise ValueError("MANUAL_REVIEW_ONLY_FOR_REFER")

        if not credit_decision.reason_codes:
            raise ValueError("REFER_REASON_CODES_MISSING")

        if not review_reason or not review_reason.strip():
            raise ValueError("MANUAL_REVIEW_REASON_REQUIRED")

        existing_review = (
            db.query(ManualReview)
            .filter(
                ManualReview.application_id == application_id,
                ManualReview.review_status.in_({
                    "OPEN",
                    "IN_PROGRESS",
                    "PENDING_CHECKER",
                }),
            )
            .order_by(ManualReview.created_at.desc())
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

    def start_review(
        self,
        db: Session,
        review: ManualReview,
        reviewer_id: str,
    ) -> ManualReview:

        if review.review_status != "OPEN":
            raise ValueError("MANUAL_REVIEW_NOT_OPEN")

        reviewer_id = reviewer_id.strip()

        if not reviewer_id:
            raise ValueError("REVIEWER_ID_REQUIRED")

        if len(reviewer_id) > 100:
            raise ValueError("REVIEWER_ID_TOO_LONG")

        review.review_status = "IN_PROGRESS"
        review.reviewer_id = reviewer_id

        return review

    def update_review_status(
        self,
        db: Session,
        review: ManualReview,
        new_status: str,
    ) -> ManualReview:

        allowed_statuses = {
        "OPEN",
        "IN_PROGRESS",
        "PENDING_CHECKER",
        "COMPLETED",
        }

        new_status = new_status.strip().upper()

        if new_status not in allowed_statuses:
            raise ValueError("INVALID_MANUAL_REVIEW_STATUS")

        current_status = review.review_status

        allowed_transitions = {
            "OPEN": {"IN_PROGRESS"},
            "IN_PROGRESS": {"PENDING_CHECKER"},
            "PENDING_CHECKER": {"COMPLETED"},
            "COMPLETED": set(),
        }

        if current_status not in allowed_transitions:
            raise ValueError("INVALID_MANUAL_REVIEW_STATUS")

        if (
            current_status == "IN_PROGRESS"
            and new_status == "COMPLETED"
            and not review.maker_checker_required
        ):
            review.review_status = new_status
            return review

        if new_status not in allowed_transitions[current_status]:
            if current_status == "COMPLETED":
                raise ValueError("MANUAL_REVIEW_ALREADY_COMPLETED")

            raise ValueError(
                f"MANUAL_REVIEW_INVALID_TRANSITION:"
                f"{current_status}->{new_status}"
            )

        review.review_status = new_status

        return review

    def submit_recommendation(
        self,
        db: Session,
        review: ManualReview,
        reviewer_id: str,
        reviewer_decision: str,
        reviewer_remarks: str | None = None,
    ) -> ManualReview:

        if review.review_status != "IN_PROGRESS":
            raise ValueError(
                "MANUAL_REVIEW_MUST_BE_IN_PROGRESS"
            )

        reviewer_id = reviewer_id.strip()

        if not reviewer_id:
            raise ValueError("REVIEWER_ID_REQUIRED")

        if len(reviewer_id) > 100:
            raise ValueError("REVIEWER_ID_TOO_LONG")

        if review.reviewer_id != reviewer_id:
            raise ValueError(
                "REVIEWER_IS_NOT_ASSIGNED"
            )

        reviewer_decision = reviewer_decision.strip().upper()

        if reviewer_decision not in {"APPROVE", "REJECT"}:
            raise ValueError("INVALID_REVIEWER_DECISION")

        review.reviewer_decision = reviewer_decision
        review.reviewer_remarks = reviewer_remarks

        if review.maker_checker_required:
            self.update_review_status(
                db=db,
                review=review,
                new_status="PENDING_CHECKER",
            )
        else:
            self.update_review_status(
                db=db,
                review=review,
                new_status="COMPLETED",
            )

        db.flush()

        return review

    def submit_checker_decision(
        self,
        db: Session,
        review: ManualReview,
        checker_id: str,
        checker_decision: str,
        checker_remarks: str | None = None,
    ) -> ManualReview:

        if review.review_status != "PENDING_CHECKER":
            raise ValueError(
                "MANUAL_REVIEW_MUST_BE_PENDING_CHECKER"
            )

        checker_id = checker_id.strip()

        if not checker_id:
            raise ValueError("CHECKER_ID_REQUIRED")

        if len(checker_id) > 100:
            raise ValueError("CHECKER_ID_TOO_LONG")

        if checker_id == review.reviewer_id:
            raise ValueError("MAKER_CANNOT_BE_CHECKER")

        checker_decision = checker_decision.strip().upper()

        if checker_decision not in {"APPROVE", "REJECT"}:
            raise ValueError("INVALID_CHECKER_DECISION")

        review.checker_id = checker_id
        review.checker_decision = checker_decision
        review.checker_remarks = checker_remarks
        review.checker_completed_at = datetime.utcnow()
        
        self.update_review_status(
            db=db,
            review=review,
            new_status="COMPLETED",
        )

        db.flush()

        return review


manual_review_service = ManualReviewService()