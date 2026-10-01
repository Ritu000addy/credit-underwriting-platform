from backend.app.schemas.borrower360 import Borrower360
from backend.app.services.fraud_validator import fraud_validator

borrower = Borrower360(
    customer_id="CUS001",

    device_behaviour={
        "device": "DEVICE_001",
        "ip": "192.0.2.10",
        "velocity": {
            "applications_last_24h": 2,
            "application_last_7d": 3,
        },
        "session_patterns": {
            "session_duration_seconds": 420,
            "multiple_devices": False,
        },
    },
)

result = fraud_validator.validate(borrower)

print(result.model_dump())