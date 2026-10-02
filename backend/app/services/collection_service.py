import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models.collection import Collection
from backend.app.models.repayment import Repayment
from backend.app.models.repayment_schedule import RepaymentSchedule

from backend.app.services.repayment_service import repayment_service
from backend.app.services.audit_log_service import audit_log_service

class CollectionService:

    def create_collection(
        self,
        db: Session,
        collection_id: str,
        application_id: str,
        collection_type: str,
        due_amount: Decimal,
        collected_amount: Decimal,
        outstanding_amount: Decimal,
        days_past_due: int,
        status: str,
        repayment_schedule_id: str | None = None,
        collection_reference: str | None = None,
        collection_channel: str | None = None,
        remarks: str | None = None,
        collected_at: datetime | None = None,
    ) -> Collection:

        if due_amount < Decimal("0.00"):
            raise ValueError("INVALID_DUE_AMOUNT")

        if collected_amount < Decimal("0.00"):
            raise ValueError("INVALID_COLLECTED_AMOUNT")

        if outstanding_amount < Decimal("0.00"):
            raise ValueError("INVALID_OUTSTANDING_AMOUNT")

        if days_past_due < 0:
            raise ValueError("INVALID_DAYS_PAST_DUE")

        if repayment_schedule_id is not None:
            schedule = (
                db.query(RepaymentSchedule)
                .filter(
                    RepaymentSchedule.repayment_schedule_id
                    == repayment_schedule_id
                )
                .first()
            )

            if schedule is None:
                raise ValueError("REPAYMENT_SCHEDULE_NOT_FOUND")

            if schedule.application_id != application_id:
                raise ValueError("APPLICATION_MISMATCH")

        if collection_reference is not None:
            existing_collection = (
                db.query(Collection)
                .filter(
                    Collection.collection_reference
                    == collection_reference
                )
                .first()
            )

            if existing_collection is not None:
                raise ValueError("COLLECTION_REFERENCE_ALREADY_EXISTS")

        collection = Collection(
            collection_id=collection_id,
            application_id=application_id,
            repayment_schedule_id=repayment_schedule_id,
            collection_type=collection_type,
            due_amount=due_amount,
            collected_amount=collected_amount,
            outstanding_amount=outstanding_amount,
            days_past_due=days_past_due,
            status=status,
            collection_reference=collection_reference,
            collection_channel=collection_channel,
            remarks=remarks,
            collected_at=collected_at,
        )

        db.add(collection)
        db.commit()
        db.refresh(collection)

        return collection

    def calculate_days_past_due(
        self,
        due_date: datetime,
        reference_date: datetime,
    ) -> int:

        if reference_date <= due_date:
            return 0

        return (reference_date.date() - due_date.date()).days

    def calculate_current_days_past_due(
        self,
        due_date: datetime,
        reference_date: datetime,
        status: str,
    ) -> int:

        if status == "PAID":
            return 0

        return self.calculate_days_past_due(
            due_date=due_date,
            reference_date=reference_date,
        )

    def get_dpd_bucket(
        self,
        days_past_due: int,
    ) -> str:

        if days_past_due < 0:
            raise ValueError("INVALID_DAYS_PAST_DUE")

        if days_past_due == 0:
            return "CURRENT"

        if days_past_due <= 30:
            return "1-30"

        if days_past_due <= 60:
            return "31-60"

        if days_past_due <= 90:
            return "61-90"

        return "90+"

    def get_collection_stage(
        self,
        days_past_due: int,
    ) -> str:

        if days_past_due < 0:
            raise ValueError("INVALID_DAYS_PAST_DUE")

        if days_past_due == 0:
            return "CURRENT"

        if days_past_due <= 30:
            return "EARLY_DELINQUENCY"

        if days_past_due <= 60:
            return "DELINQUENCY"

        if days_past_due <= 90:
            return "SERIOUS_DELINQUENCY"

        return "SEVERE_DELINQUENCY"
    
    def record_collection(
        self,
        db: Session,
        collection_id: str,
        application_id: str,
        repayment_schedule_id: str,
        repayment_amount: Decimal,
        collection_reference: str | None = None,
        collection_channel: str | None = None,
        payment_mode: str | None = None,
        payment_provider: str | None = None,
        remarks: str | None = None,
    ) -> Collection:

        schedule = (
            db.query(RepaymentSchedule)
            .filter(
                RepaymentSchedule.repayment_schedule_id
                == repayment_schedule_id
            )
            .first()
        )

        if schedule is None:
            raise ValueError("REPAYMENT_SCHEDULE_NOT_FOUND")

        if schedule.application_id != application_id:
            raise ValueError("APPLICATION_MISMATCH")

        repayment = repayment_service.record_repayment(
            db=db,
            repayment_id=f"REPAY-{uuid.uuid4().hex[:20]}",
            application_id=application_id,
            repayment_schedule_id=repayment_schedule_id,
            repayment_amount=repayment_amount,
            repayment_reference=collection_reference,
            payment_mode=payment_mode,
            payment_provider=payment_provider,
        )

        total_collected = (
            db.query(Repayment)
                .filter(
                    Repayment.repayment_schedule_id == repayment_schedule_id,
                    Repayment.status == "SUCCESS",
                )
                .with_entities(
                    Repayment.repayment_amount
                )
                .all()
        )

        total_collected_amount = sum(
            (amount for (amount,) in total_collected),
            Decimal("0.00"),
        )

        outstanding_amount = (
            schedule.total_due - total_collected_amount
        )

        collection_status = (
            "COLLECTED"
            if outstanding_amount == Decimal("0.00")
            else "PARTIAL"
        )

        collection = (
            db.query(Collection)
            .filter(
                Collection.repayment_schedule_id == repayment_schedule_id
            )
            .order_by(Collection.created_at.desc())
            .first()
        )

        previous_collection_status = (
            collection.status if collection is not None else "NOT_CREATED"
        )

        if collection is None:
            days_past_due = self.calculate_days_past_due(
                due_date=schedule.due_date,
                reference_date=repayment.paid_at,
            )

            collection = Collection(
                collection_id=collection_id,
                application_id=application_id,
                repayment_schedule_id=repayment_schedule_id,
                collection_type="EMI",
                due_amount=schedule.total_due,
                collected_amount=total_collected_amount,
                outstanding_amount=outstanding_amount,
                days_past_due=days_past_due,
                status=collection_status,
                collection_reference=collection_reference,
                collection_channel=collection_channel,
                remarks=remarks,
                collected_at=repayment.paid_at,
            )
            db.add(collection)
        else:
            collection.collected_amount = total_collected_amount
            collection.outstanding_amount = outstanding_amount
            collection.status = collection_status
            collection.collection_reference = collection_reference
            collection.collection_channel = collection_channel
            collection.remarks = remarks
            collection.collected_at = repayment.paid_at

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=application_id,
            actor_type="SYSTEM",
            action="COLLECTION_RECORDED",
            entity_type="COLLECTION",
            entity_reference=collection.collection_id,
            description=(
                f"Collection recorded with status "
                f"{collection.status}; "
                f"collected amount {collection.collected_amount}; "
                f"outstanding amount {collection.outstanding_amount}; "
                f"DPD {collection.days_past_due}"
            ),
            previous_state=previous_collection_status,
            new_state=collection.status,
            request_reference=collection_reference,
        )

        db.commit()
        db.refresh(collection)

        return collection

    def get_collections_by_application(
        self,
        db: Session,
        application_id: str,
    ) -> list[Collection]:

        return (
            db.query(Collection)
            .filter(
                Collection.application_id == application_id,
            )
            .order_by(
                Collection.created_at,
            )
            .all()
        )

    def get_collections_by_schedule(
        self,
        db: Session,
        application_id: str,
        repayment_schedule_id: str,
    ) -> list[Collection]:

        return (
            db.query(Collection)
            .filter(
                Collection.application_id == application_id,
                Collection.repayment_schedule_id == repayment_schedule_id,
            )
            .order_by(
                Collection.created_at,
            )
            .all()
        )

    def get_collection_summary(
        self,
        db: Session,
        application_id: str,
        repayment_schedule_id: str,
    ) -> dict:

        collections = self.get_collections_by_schedule(
            db=db,
            application_id=application_id,
            repayment_schedule_id=repayment_schedule_id,
        )

        if not collections:
            return {
                "application_id": application_id,
                "repayment_schedule_id": repayment_schedule_id,
                "total_due": Decimal("0.00"),
                "total_collected": Decimal("0.00"),
                "total_outstanding": Decimal("0.00"),
                "days_past_due": 0,
                "status": None,
            }

        latest_collection = max(
            collections,
            key=lambda collection: collection.created_at,
        )

        return {
            "application_id": application_id,
            "repayment_schedule_id": repayment_schedule_id,
            "total_due": latest_collection.due_amount,
            "total_collected": latest_collection.collected_amount,
            "total_outstanding": latest_collection.outstanding_amount,
            "days_past_due": latest_collection.days_past_due,
            "status": latest_collection.status,
        }

collection_service = CollectionService()