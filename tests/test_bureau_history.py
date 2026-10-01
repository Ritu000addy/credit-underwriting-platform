from backend.app.schemas.borrower360 import Borrower360
from backend.app.services.bureau_history_validator import bureau_history_validator

borrower = Borrower360(
    customer_id="CUS001",

    credit_bureau={
        "score": 750,
        "dpd": 0,
        "enquiries": 2,
        "active_loans": 1,
        "write_offs": 0,
    },

    internal_history={
        "past_loans": [
            {
                "load_id": "LOAN001",
                "status": "CLOSED",
            }
        ],
        "repayment": [
            {
                "load_id": "LOAN001",
                "status": "ON_TIME",
            }
        ],
        "dpd": [],
        "collections": [],
    },
)

result = bureau_history_validator.validate(borrower)

print(result.model_dump())