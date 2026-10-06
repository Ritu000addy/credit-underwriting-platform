from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from backend.app.database import SessionLocal
from backend.app.services.collection_service import collection_service


def unique(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10].upper()}"


def test_collection_persistence():
    db = SessionLocal()

    try:
        collection_id = unique("DEV-COLLECTION")
        collection_reference = unique("COLLECTION-REF")

        collection = collection_service.create_collection(
            db=db,
            collection_id=collection_id,
            application_id="PERSIST-TEST-001",
            repayment_schedule_id="DEV-ORCH-REPAYMENT-001",
            collection_type="REGULAR_REPAYMENT",
            due_amount=Decimal("13327.32"),
            collected_amount=Decimal("13327.32"),
            outstanding_amount=Decimal("0"),
            days_past_due=0,
            status="COLLECTED",
            collection_reference=collection_reference,
            collection_channel="NACH",
            remarks="Development test collection",
            collected_at=datetime(2026, 10, 25),
        )

        assert collection.collection_id == collection_id
        assert collection.application_id == "PERSIST-TEST-001"
        assert (
            collection.repayment_schedule_id
            == "DEV-ORCH-REPAYMENT-001"
        )
        assert collection.collection_type == "REGULAR_REPAYMENT"
        assert collection.due_amount == Decimal("13327.32")
        assert collection.collected_amount == Decimal("13327.32")
        assert collection.outstanding_amount == Decimal("0")
        assert collection.days_past_due == 0
        assert collection.status == "COLLECTED"
        assert collection.collection_reference == collection_reference
        assert collection.collection_channel == "NACH"
        assert collection.collected_at == datetime(2026, 10, 25)

    finally:
        db.close()