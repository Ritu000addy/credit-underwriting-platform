from decimal import Decimal
from datetime import datetime

from backend.app.database import SessionLocal
from backend.app.services.post_disbursement_service import (
    post_disbursement_service,
)


db = SessionLocal()

try:
    sanction = post_disbursement_service.create_sanction(
        db=db,
        application_id="PERSIST-TEST-001",
        sanction_id="DEV-ORCH-SANCTION-001",
        sanctioned_amount=Decimal("150000"),
        sanctioned_tenure=12,
        sanctioned_emi=Decimal("13327.32"),
        interest_rate=Decimal("12"),
        approval_authority="DEV-TEST",
        terms_and_conditions="Development test sanction",
    )

    print("SANCTION CREATED")
    print("sanction_id:", sanction.sanction_id)

    mandate = post_disbursement_service.create_mandate(
        db=db,
        application_id="PERSIST-TEST-001",
        mandate_id="DEV-ORCH-MANDATE-001",
        status="COMPLETED",
        mandate_reference="MANDATE-REF-001",
        mandate_type="NACH",
        provider="DEV-PROVIDER",
    )

    print("MANDATE CREATED")
    print("mandate_id", mandate.mandate_id)

    disbursement = post_disbursement_service.create_disbursement(
        db=db,
        application_id="PERSIST-TEST-001",
        disbursement_id="DEV-ORCH-DISBURSEMENT-001",
        disbursement_amount=Decimal("150000"),
        sanction_id="DEV-ORCH-SANCTION-001",
        beneficiary_reference="BENEFICIARY-REF-001",
        bank_reference="BANK-REF-001",
        payment_provider="DEV-PAYMENT-PROVIDER",
    )

    print("DISBURSEMENT CREATED")
    print("disbursement_id:", disbursement.disbursement_id)

    print("application_id:", disbursement.application_id)
    print("sanction_id:", disbursement.sanction_id)
    print("disbursement_amount:", disbursement.disbursement_amount)
    print("status:", disbursement.status)

    installment = post_disbursement_service.create_repayment_schedule(
        db=db,
        repayment_schedule_id="DEV-ORCH-REPAYMENT-002",
        application_id="PERSIST-TEST-001",
        disbursement_id="DEV-ORCH-DISBURSEMENT-001",
        installment_number=2,
        due_date=datetime(2026, 11, 25),
        principal_due=Decimal("12000.00"),
        interest_due=Decimal("1327.32"),
        total_due=Decimal("13327.32"),
        outstanding_principal=Decimal("126172.68"),
    )

    print("REPAYMENT SCHEDULE ORCHESTRATED")
    print("repayment_schedule_id:", installment.repayment_schedule_id)
    print("installment_number:", installment.installment_number)
    print("total_due:", installment.total_due)
    print("outstanding_principal:", installment.outstanding_principal)
    print("status:", installment.status)

finally:
    db.close()