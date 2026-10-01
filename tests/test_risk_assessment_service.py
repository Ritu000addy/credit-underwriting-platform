from backend.app.schemas.application import ApplicationCreate
from backend.app.schemas.borrower360 import (
    Borrower360,
    KYCData,
    CreditBureauData,
    BankCashFlowData,
    EmploymentBusinessData,
    InternalHistoryData,
    DeviceBehaviourData,
    DocumentData,
)
from backend.app.services.risk_assessment_service import risk_assessment_service

application = ApplicationCreate(
    application_id="APP001",
    customer_id="CUS001",
    requested_amount=500000,
    loan_tenure_months=36,
)

borrower = Borrower360(
    customer_id="CUS001",

    kyc=KYCData(
        pan="ABCDE1234F",
        aadhaar="XXXXXXXX1234",
        ekyc_result="SUCCESS",
        address="Pune",
    ),

    credit_bureau=CreditBureauData(
        score=742,
        dpd=0,
        enquiries=2,
        active_loans=2,
        total_outstanding=250000,
        write_offs=0,
    ),

    bank_cash_flow=BankCashFlowData(
        credits=80000,
        debits=45000,
        balance=120000,
        emi=15000,
        bounce=0,
        transaction_count=120,
        income_pattern={
            "trend": "STABLE"
        },
    ),

    employment_business=EmploymentBusinessData(
        salary=80000,
        employer="Synthetic Employer",
    ),

    internal_history=InternalHistoryData(
        past_loans=[
            {"loan_id": "L001"},
            {"loan_id": "L002"},
        ],
        repayment=[
            {"loan_id": "L001", "status": "ON_TIME"},
            {"loan_id": "L002", "status": "ON_TIME"},
        ],
        dpd=[],
        collections=[],
    ),

    device_behaviour=DeviceBehaviourData(
        device="SYNTHETIC_DEVICE",
        ip="192.0.2.1",
        velocity={"applications_last_24h": 1},
        session_patterns={"normal": True}
    ),

    documents=DocumentData(
        payslips=[],
        bank_statements=[],
        invoices=[],
        business_proofs=[],
    ),
)

result = risk_assessment_service.assess(
    application,
    borrower,
)

print(result.model_dump())