from decimal import Decimal

from backend.app.database import SessionLocal
from backend.app.services.disbursement_service import disbursement_service


db = SessionLocal()

try:
    disbursement = disbursement_service.create_disbursement(
        db=db,
        disbursement_id="DISB-RETRY-TEST-001",
        application_id="PERSIST-TEST-001",
        disbursement_amount=Decimal("50000"),
        status="FAILED",
        idempotency_key="IDEMP-RETRY-TEST-001",
        sanction_id="DEV-ORCH-SANCTION-001",
        beneficiary_reference="BEN-API-TEST-001",
        payment_provider="DEV-BANK-PROVIDER",
        failure_reason="BANK_TIMEOUT",
    )

    print("DISBURSEMENT CREATED")
    print("ID:", disbursement.disbursement_id)
    print("STATUS:", disbursement.status)
    print("FAILURE:", disbursement.failure_reason)

finally:
    db.close()