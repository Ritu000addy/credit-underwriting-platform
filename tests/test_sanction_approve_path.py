from decimal import Decimal

from backend.app.database import SessionLocal
from backend.app.models.credit_decision import CreditDecision
from backend.app.models.loan_application import LoanApplication
from backend.app.models.customer import Customer
from backend.app.services.sanction_service import sanction_service


APPLICATION_ID = "SANCTION-APPROVE-TEST-001"
CUSTOMER_ID = "SANCTION-CUSTOMER-001"
DECISION_ID = "DEC-SANCTION-APPROVE-001"
SANCTION_ID = "SAN-APPROVE-TEST-001"


db = SessionLocal()

try:
    customer = db.get(Customer, CUSTOMER_ID)

    if customer is None:
        customer = Customer(
            customer_id=CUSTOMER_ID,
            kyc_status="VERIFIED",
        )
        db.add(customer)
        db.flush()

    application = db.get(LoanApplication, APPLICATION_ID)

    if application is None:
        application = LoanApplication(
            application_id=APPLICATION_ID,
            customer_id=CUSTOMER_ID,
            product="DEV-TEST",
            requested_amount=Decimal("150000.00"),
            status="APPROVED",
        )
        db.add(application)
        db.flush()

    decision = db.get(CreditDecision, DECISION_ID)

    if decision is None:
        decision = CreditDecision(
            decision_id=DECISION_ID,
            application_id=APPLICATION_ID,
            credit_score=750,
            risk_grade="A",
            probability_of_default=Decimal("0.020000"),
            affordability_score=Decimal("90.0000"),
            repayment_propensity=Decimal("95.0000"),
            fraud_score=Decimal("5.0000"),
            income_stability_score=Decimal("85.0000"),
            recommended_amount=Decimal("150000.00"),
            recommended_tenure=12,
            recommended_emi=Decimal("13327.32"),
            foir=Decimal("35.0000"),
            risk_segment="LOW_RISK",
            decision="APPROVE",
            confidence=Decimal("0.950000"),
            reason_codes="DEVELOPMENT_TEST_APPROVAL",
            model_version="DEV-TEST",
            policy_version="DEV-TEST",
        )
        db.add(decision)
        db.commit()

    sanction = sanction_service.create_sanction(
        db=db,
        sanction_id=SANCTION_ID,
        application_id=APPLICATION_ID,
        sanctioned_amount=Decimal("150000.00"),
        sanctioned_tenure=12,
        sanctioned_emi=Decimal("13327.32"),
        interest_rate=Decimal("12.0000"),
        sanction_status="APPROVED",
        approval_authority="DEV-TEST",
        terms_and_conditions="Development approval-path test",
    )

    print("SANCTION CREATED")
    print("sanction_id:", sanction.sanction_id)
    print("application_id:", sanction.application_id)
    print("status:", sanction.sanction_status)

finally:
    db.close()