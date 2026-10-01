from backend.app.schemas.borrower360 import Borrower360
from backend.app.services.bank_income_validator import bank_income_validator

borrower = Borrower360(
    customer_id="CUS001",

    bank_cash_flow={
        "credits": 85000,
        "debits": 45000,
        "balance": 120000,
        "emi": 18000,
        "bounce": 0,
        "income_pattern": {
            "monthly_average": 85000,
            "trend": "STABLE",
        },
    },

    employment_business={
        "salary": 80000,
        "employer": "ABC Technologies",
        "gst": None,
        "udyam": None,
        "business_vintage": None,
    },
)

result = bank_income_validator.validate(borrower)

print(result.model_dump())