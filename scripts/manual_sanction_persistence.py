from decimal import Decimal

from backend.app.database import SessionLocal
from backend.app.services.sanction_service import sanction_service


db = SessionLocal()

try:
    result = sanction_service.create_sanction(
        db=db,
        sanction_id="DEV-SANCTION-001",
        application_id="PERSIST-TEST-001",
        sanctioned_amount=Decimal("150000"),
        sanctioned_tenure=12,
        sanctioned_emi=Decimal("13328.81"),
        interest_rate=Decimal("12.0000"),
        sanction_status="APPROVED",
        approval_authority="DEV_TEST",
        terms_and_conditions="Development sanction persistence test.",
    )

    print("SANCTION SAVED")
    print("sanction_id:", result.sanction_id)
    print("application_id:", result.application_id)
    print("sanctioned_amount:", result.sanctioned_amount)
    print("sanctioned_tenure:", result.sanctioned_tenure)
    print("sanctioned_emi:", result.sanctioned_emi)
    print("interest_rate:", result.interest_rate)
    print("sanction_status:", result.sanction_status)
    print("approval_authority:", result.approval_authority)
    print("terms_and_conditions:", result.terms_and_conditions)

finally:
    db.close()