from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.fraud import FraudScreeningResult

class FraudValidator:
    def validate(
        self,
        borrower: Borrower360,
    ) -> FraudScreeningResult:

        checks: list[dict] = []
        reason_codes: list[str] = []

        device_data = borrower.device_behaviour

        if device_data is None:
            return FraudScreeningResult(
                status="REFER",
                checks=[
                    {
                        "check_id": "DEVICE_BEHAVIOUR_DATA",
                        "status": "NOT_AVAILABLE",
                        "reason": "Device/behaviour data not available",
                    }
                ],
                reason_codes=["FRAUD_DATA_DEVICE_BEHAVIOUR_DATA"],
            )

        # Device

        if device_data.device:
            checks.append(
                {
                    "check_id": "DEVICE",
                    "status": "AVAILABLE",
                    "reason": "Device information available"
                }
            )
        else:
            checks.append(
                {
                    "check_id": "DEVICE",
                    "status": "NOT_AVAILABLE",
                    "reason": "Device information not available"
                }
            )

        # IP
          
        if device_data.ip:
            checks.append(
                {
                    "check_id": "IP",
                    "status": "AVAILABLE",
                    "reason": "IP information available"
                }
            )
        else:
            checks.append(
                {
                    "check_id": "IP",
                    "status": "NOT_AVAILABLE",
                    "reason": "IP information not available"
                }
            )

        # Velocity

        if device_data.velocity is not None:
            checks.append(
                {
                    "check_id": "VELOCITY",
                    "status": "AVAILABLE",
                    "reason": "Application velocity information available"
                }
            )
        else:
            checks.append(
                {
                    "check_id": "VELOCITY",
                    "status": "NOT_AVAILABLE",
                    "reason": "Application velocity information not available"
                }
            )

        # Session Patterns

        if device_data.session_patterns is not None:
            checks.append(
                {
                    "check_id": "SESSION_PATTERNS",
                    "status": "AVAILABLE",
                    "reason": "Session patterns information available"
                }
            )
        else:
            checks.append(
                {
                    "check_id": "SESSION_PATTERNS",
                    "status": "NOT_AVAILABLE",
                    "reason": "Session patterns information not available"
                }
            )
        
        for check in checks:
            if check["status"] == "NOT_AVAILABLE":
                reason_codes.append(
                    f"FRAUD_DATA_{check['check_id']}"
                )

        status = "REFER" if reason_codes else "PASS"

        return FraudScreeningResult(
            status=status,
            checks=checks,
            reason_codes=reason_codes,
        )

fraud_validator = FraudValidator()