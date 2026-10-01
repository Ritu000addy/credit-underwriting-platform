import uuid

from sqlalchemy.orm import Session

from backend.app.models.internal_history import InternalHistory
from backend.app.schemas.internal_history import InternalHistoryCreate


class InternalHistoryService:

    def create_internal_history(
        self,
        db: Session,
        history: InternalHistoryCreate,
    ):
        record = InternalHistory(
            internal_history_id=f"INT-{uuid.uuid4().hex[:12].upper()}",
            application_id=history.application_id,
            previous_loans_count=history.previous_loans_count,
            active_loans_count=history.active_loans_count,
            closed_loans_count=history.closed_loans_count,
            total_previous_exposure=history.total_previous_exposure,
            total_outstanding_amount=history.total_outstanding_amount,
            repayment_history=history.repayment_history,
            dpd_count=history.dpd_count,
            max_dpd=history.max_dpd,
            overdue_amount=history.overdue_amount,
            write_off_count=history.write_off_count,
            settlement_count=history.settlement_count,
            last_loan_date=history.last_loan_date,
            analysis_reference=history.analysis_reference,
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return record


internal_history_service = InternalHistoryService()