from backend.app.schemas.borrower360 import Borrower360

borrower = Borrower360(
    customer_id="CUS001",
    kyc={
        "pan": "ABCDE1234F",
        "dob": "1993-03-01",
        "ekyc_result": "VERIFIED",
    },
    credit_bureau={
        "score": 750,
        "dpd": 0,
        "enquiries": 2,
        "active_loans": 1,
    },
    bank_cash_flow={
        "credits": 100000,
        "debits": 40000,
        "balance": 60000,
        "emi": 15000,
        "bounce": 0
    },
    employment_business={
        "salary": 75000,
        "employer": "ABC Company",
    },
)

print(borrower.model_dump())