from datetime import datetime
from decimal import Decimal

from backend.app.database import SessionLocal
from backend.app.services.collection_service import collection_service


db = SessionLocal()

try:
    collection = collection_service.create_collection(
        db=db,
        collection_id="DEV-ORCH-COLLECTION-001",
        application_id="PERSIST-TEST-001",
        repayment_schedule_id="DEV-ORCH-REPAYMENT-001",
        collection_type="REGULAR_REPAYMENT",
        due_amount=Decimal("13327.32"),
        collected_amount=Decimal("13327.32"),
        outstanding_amount=Decimal("0"),
        days_past_due=0,
        status="COLLECTED",
        collection_reference="COLLECTION-REF-001",
        collection_channel="NACH",
        remarks="Development test collection",
        collected_at=datetime(2026, 10, 25),
    )

    print("COLLECTION CREATED")
    print("collection_id:", collection.collection_id)
    print("application_id:", collection.application_id)
    print("repayment_schedule_id:", collection.repayment_schedule_id)
    print("collection_type:", collection.collection_type)
    print("due_amount:", collection.due_amount)
    print("collected_amount:", collection.collected_amount)
    print("outstanding_amount:", collection.outstanding_amount)
    print("days_past_due:", collection.days_past_due)
    print("status:", collection.status)
    print("collection_reference:", collection.collection_reference)
    print("collection_channel:", collection.collection_channel)
    print("collected_at:", collection.collected_at)

finally:
    db.close()