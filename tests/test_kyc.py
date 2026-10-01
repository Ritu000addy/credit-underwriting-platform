from backend.app.schemas.borrower360 import Borrower360
from backend.app.services.kyc_validator import kyc_validator

borrower = Borrower360(
    customer_id="CUS001",
    kyc={
        "pan": "ABCDE1234F",
        "aadhaar": "123456789012",
        "ekyc_result": "VERIFIED",
        "dob": "1993-03-01",
        "address": "Pune",
    },
)

result = kyc_validator.validate(borrower)

print(result.model_dump())