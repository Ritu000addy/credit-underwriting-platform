from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.loan_application import LoanApplication
from backend.app.models.credit_decision import CreditDecision
from backend.app.models.manual_review import ManualReview
from backend.app.models.review_exception import ReviewException
from backend.app.models.sanction import Sanction
from backend.app.models.agreement import Agreement
from backend.app.models.mandate import Mandate
from backend.app.models.disbursement import Disbursement
from backend.app.models.repayment import Repayment
from backend.app.models.collection import Collection
from backend.app.models.reconciliation import Reconciliation
from backend.app.models.operations_queue import OperationsQueue


class OperationsService:

    @staticmethod
    def _status_counts(
        db: Session,
        model,
        status_column,
    ) -> dict:
        rows = (
            db.query(
                status_column,
                func.count(),
            )
            .group_by(status_column)
            .order_by(status_column)
            .all()
        )

        by_status = {
            status or "UNKNOWN": int(count)
            for status, count in rows
        }

        return {
            "total": sum(by_status.values()),
            "by_status": by_status,
        }

    @staticmethod
    def _latest(
        db: Session,
        model,
        application_id: str,
        order_column,
    ):
        return (
            db.query(model)
            .filter(
                model.application_id == application_id
            )
            .order_by(order_column.desc())
            .first()
        )

    def get_dashboard(
        self,
        db: Session,
    ) -> dict:
        overdue_filter = (
            (Collection.days_past_due > 0)
            & (Collection.outstanding_amount > 0)
        )

        overdue_schedule_count = (
            db.query(
                func.count(
                    func.distinct(
                        Collection.repayment_schedule_id
                    )
                )
            )
            .filter(overdue_filter)
            .scalar()
            or 0
        )

        overdue_application_count = (
            db.query(
                func.count(
                    func.distinct(
                        Collection.application_id
                    )
                )
            )
            .filter(overdue_filter)
            .scalar()
            or 0
        )

        overdue_outstanding_amount = (
            db.query(
                func.coalesce(
                    func.sum(
                        Collection.outstanding_amount
                    ),
                    0,
                )
            )
            .filter(overdue_filter)
            .scalar()
            or Decimal("0")
        )

        return {
            "generated_at": datetime.now(
                timezone.utc
            ),
            "applications": self._status_counts(
                db,
                LoanApplication,
                LoanApplication.status,
            ),
            "underwriting": self._status_counts(
                db,
                CreditDecision,
                CreditDecision.decision,
            ),
            "manual_review": self._status_counts(
                db,
                ManualReview,
                ManualReview.review_status,
            ),
            "exceptions": self._status_counts(
                db,
                ReviewException,
                ReviewException.status,
            ),
            "disbursements": self._status_counts(
                db,
                Disbursement,
                Disbursement.status,
            ),
            "collections": {
                "overdue_schedule_count": int(
                    overdue_schedule_count
                ),
                "overdue_application_count": int(
                    overdue_application_count
                ),
                "overdue_outstanding_amount": (
                    overdue_outstanding_amount
                ),
            },
            "reconciliation": self._status_counts(
                db,
                Reconciliation,
                Reconciliation.reconciliation_status,
            ),
            "operations_queue": self._status_counts(
                db,
                OperationsQueue,
                OperationsQueue.queue_status,
            ),
        }

    def _application_summary(
        self,
        db: Session,
        application: LoanApplication,
    ) -> dict:
        application_id = application.application_id

        decision = self._latest(
            db,
            CreditDecision,
            application_id,
            CreditDecision.created_at,
        )

        review = self._latest(
            db,
            ManualReview,
            application_id,
            ManualReview.created_at,
        )

        exception = self._latest(
            db,
            ReviewException,
            application_id,
            ReviewException.created_at,
        )

        sanction = self._latest(
            db,
            Sanction,
            application_id,
            Sanction.created_at,
        )

        agreement = self._latest(
            db,
            Agreement,
            application_id,
            Agreement.created_at,
        )

        mandate = self._latest(
            db,
            Mandate,
            application_id,
            Mandate.created_at,
        )

        disbursement = self._latest(
            db,
            Disbursement,
            application_id,
            Disbursement.created_at,
        )

        repayment = self._latest(
            db,
            Repayment,
            application_id,
            Repayment.created_at,
        )

        collection = self._latest(
            db,
            Collection,
            application_id,
            Collection.created_at,
        )

        reconciliation = self._latest(
            db,
            Reconciliation,
            application_id,
            Reconciliation.created_at,
        )

        return {
            "application_id": application.application_id,
            "customer_id": application.customer_id,
            "product": application.product,
            "requested_amount": application.requested_amount,
            "status": application.status,
            "created_at": application.created_at,
            "updated_at": application.updated_at,

            "decision": (
                decision.decision
                if decision is not None
                else None
            ),
            "risk_grade": (
                decision.risk_grade
                if decision is not None
                else None
            ),
            "policy_version": (
                decision.policy_version
                if decision is not None
                else None
            ),

            "manual_review_status": (
                review.review_status
                if review is not None
                else None
            ),
            "exception_status": (
                exception.status
                if exception is not None
                else None
            ),

            "sanction_status": (
                sanction.sanction_status
                if sanction is not None
                else None
            ),

            "agreement_status": (
                agreement.agreement_status
                if agreement is not None
                else None
            ),
            "esign_status": (
                agreement.esign_status
                if agreement is not None
                else None
            ),

            "mandate_status": (
                mandate.status
                if mandate is not None
                else None
            ),

            "disbursement_status": (
                disbursement.status
                if disbursement is not None
                else None
            ),
            "disbursement_amount": (
                disbursement.disbursement_amount
                if disbursement is not None
                else None
            ),

            "repayment_status": (
                repayment.status
                if repayment is not None
                else None
            ),

            "collection_status": (
                collection.status
                if collection is not None
                else None
            ),
            "overdue_amount": (
                collection.outstanding_amount
                if (
                    collection is not None
                    and collection.days_past_due > 0
                )
                else None
            ),
            "days_past_due": (
                collection.days_past_due
                if collection is not None
                else None
            ),

            "reconciliation_status": (
                reconciliation.reconciliation_status
                if reconciliation is not None
                else None
            ),
        }

    def list_applications(
        self,
        db: Session,
        application_id: str | None = None,
        customer_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        query = db.query(LoanApplication)

        if application_id is not None:
            query = query.filter(
                LoanApplication.application_id
                == application_id
            )

        if customer_id is not None:
            query = query.filter(
                LoanApplication.customer_id
                == customer_id
            )

        if status is not None:
            query = query.filter(
                LoanApplication.status == status
            )

        total = query.count()

        applications = (
            query
            .order_by(
                LoanApplication.updated_at.desc()
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [
                self._application_summary(
                    db,
                    application,
                )
                for application in applications
            ],
        }

    def get_application(
        self,
        db: Session,
        application_id: str,
    ) -> dict | None:
        application = db.get(
            LoanApplication,
            application_id,
        )

        if application is None:
            return None

        return self._application_summary(
            db,
            application,
        )

    def list_manual_reviews(
        self,
        db: Session,
        review_status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ):
        query = db.query(ManualReview)

        if review_status is not None:
            query = query.filter(
                ManualReview.review_status
                == review_status
            )

        return (
            query
            .order_by(
                ManualReview.updated_at.desc()
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

    def list_exceptions(
        self,
        db: Session,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ):
        query = db.query(ReviewException)

        if status is not None:
            query = query.filter(
                ReviewException.status == status
            )

        return (
            query
            .order_by(
                ReviewException.updated_at.desc()
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

    def list_disbursements(
        self,
        db: Session,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ):
        query = db.query(Disbursement)

        if status is not None:
            query = query.filter(
                Disbursement.status == status
            )

        return (
            query
            .order_by(
                Disbursement.updated_at.desc()
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

    def list_reconciliation(
        self,
        db: Session,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ):
        query = db.query(Reconciliation)

        if status is not None:
            query = query.filter(
                Reconciliation.reconciliation_status
                == status
            )

        return (
            query
            .order_by(
                Reconciliation.updated_at.desc()
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

    def list_overdue_collections(
        self,
        db: Session,
        limit: int = 50,
        offset: int = 0,
    ):
        return (
            db.query(Collection)
            .filter(
                Collection.days_past_due > 0,
                Collection.outstanding_amount > 0,
            )
            .order_by(
                Collection.days_past_due.desc(),
                Collection.updated_at.desc(),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )


operations_service = OperationsService()