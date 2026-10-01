from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models.repayment_schedule import RepaymentSchedule
from backend.app.services.collection_service import collection_service


class OverdueService:

    def get_overdue_schedules(
        self,
        db: Session,
        reference_date: datetime,
    ) -> list[dict]:

        schedules = (
            db.query(RepaymentSchedule)
            .filter(
                RepaymentSchedule.status == "PENDING",
                RepaymentSchedule.due_date < reference_date,
            )
            .order_by(
                RepaymentSchedule.due_date,
            )
            .all()
        )

        overdue_schedules = []

        for schedule in schedules:
            days_past_due = (
                collection_service.calculate_current_days_past_due(
                    due_date=schedule.due_date,
                    reference_date=reference_date,
                    status=schedule.status,
                )
            )

            dpd_bucket = collection_service.get_dpd_bucket(
                days_past_due
            )

            collection_stage = collection_service.get_collection_stage(
                days_past_due
            )

            overdue_schedules.append(
                {
                    "repayment_schedule_id": schedule.repayment_schedule_id,
                    "application_id": schedule.application_id,
                    "installment_number": schedule.installment_number,
                    "due_date": schedule.due_date,
                    "total_due": schedule.total_due,
                    "days_past_due": days_past_due,
                    "dpd_bucket": dpd_bucket,
                    "collection_stage": collection_stage,
                    "status": schedule.status,
                }
            )

        return overdue_schedules

    def get_application_overdue_summary(
        self,
        db: Session,
        application_id: str,
        reference_date: datetime,
    ) -> dict:

        overdue_schedules = self.get_overdue_schedules(
            db=db,
            reference_date=reference_date,
        )

        application_overdue = [
            schedule
            for schedule in overdue_schedules
            if schedule["application_id"] == application_id
        ]

        if not application_overdue:
            return {
                "application_id": application_id,
                "total_overdue_installments": 0,
                "total_overdue_amount": 0,
                "maximum_days_past_due": 0,
                "current_dpd_bucket": "CURRENT",
                "collection_stage": "CURRENT",
                "oldest_overdue_due_date": None,
            }

        total_overdue_amount = sum(
            (
                schedule["total_due"]
                for schedule in application_overdue
            ),
            Decimal("0.00"),
        )

        maximum_days_past_due = max(
            schedule["days_past_due"]
            for schedule in application_overdue
        )

        oldest_overdue_due_date = min(
            schedule["due_date"]
            for schedule in application_overdue
        )

        return {
            "application_id": application_id,
            "total_overdue_installments": len(application_overdue),
            "total_overdue_amount": total_overdue_amount,
            "maximum_days_past_due": maximum_days_past_due,
            "current_dpd_bucket": collection_service.get_dpd_bucket(
                maximum_days_past_due
            ),
            "collection_stage": collection_service.get_collection_stage(
                maximum_days_past_due
            ),
            "oldest_overdue_due_date": oldest_overdue_due_date,
        }

overdue_service = OverdueService()