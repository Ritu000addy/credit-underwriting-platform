from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.kyc import KYCCheckResult

class KYCValidator:

    def validate(
        self,
        borrower: Borrower360,
        kyc_config: dict | None = None,
    ) -> KYCCheckResult:

        config = kyc_config or {}

        pan_required = config.get("pan_required", True)
        ekyc_required = config.get("ekyc_required", True)
        required_ekyc_result = str(
            config.get("required_ekyc_result", "VERIFIED")
        ).strip().upper()
        aadhaar_kyc_required = config.get(
            "aadhaar_kyc_required",
            False,
        )

        checks: list[dict] = []
        reason_codes: list[str] = []

        kyc = borrower.kyc

        # KYC data availability
        if kyc is None:
            return KYCCheckResult(
                status= "FAIL",
                checks=[
                    {
                        "check_id": "KYC_DATA",
                        "status": "FAIL",
                        "reason": "KYC data not available",
                    }
                ],
                reason_codes=["KYC_DATA_MISSING"],
            )
        
        # PAN: required according to the active policy.
        if kyc.pan:
            checks.append(
                {
                    "check_id": "PAN",
                    "status": "PASS",
                    "reason": "PAN information available",
                }
            )
        elif pan_required:
            checks.append(
                {
                    "check_id": "PAN",
                    "status": "FAIL",
                    "reason": "PAN information missing",
                }
            )
            reason_codes.append("KYC_PAN_MISSING")
        else:
            checks.append({
                "check_id": "PAN",
                "status": "NOT_REQUIRED",
                "reason": "PAN is not required by the active policy",
            })

        
        # e-KYC: a provided result must match the configured result.
        ekyc_result = (
            kyc.ekyc_result.strip().upper()
            if kyc.ekyc_result
            else None
        )

        if ekyc_result == required_ekyc_result:
            checks.append(
                {
                    "check_id": "EKYC",
                    "status": "PASS",
                    "reason": "Required e-KYC result verified",
                }
            )
        elif not ekyc_result and not ekyc_required:
            checks.append({
                "check_id": "EKYC",
                "status": "NOT_REQUIRED",
                "reason": "e-KYC is not required by the active policy",
            })
        else:
            checks.append(
                {
                    "check_id": "EKYC",
                    "status": "FAIL",
                    "reason": (
                        "e-KYC result missing"
                        if not ekyc_result
                        else "e-KYC result does not match the required result"
                    ),
                }
            )
            if not ekyc_result:
                reason_codes.append("KYC_EKYC_MISSING")
            elif ekyc_result == "PENDING":
                reason_codes.append("KYC_EKYC_PENDING")
            else:
                reason_codes.append("KYC_EKYC_NOT_VERIFIED")

        # Aadhaar: fail only when the active policy requires verification.
        aadhaar_status = (
            kyc.aadhaar_kyc_status.strip().upper()
            if kyc.aadhaar_kyc_status
            else None
        )

        if aadhaar_status == "VERIFIED":
            checks.append(
                {
                    "check_id": "AADHAAR_KYC",
                    "status": "PASS",
                    "reason": "Aadhaar KYC verification passed",
                }
            )
        elif not aadhaar_kyc_required:
            checks.append({
                "check_id": "AADHAAR_KYC",
                "status": "NOT_REQUIRED",
                "reason": "Aadhaar KYC is not required by the active policy",
            })
        else:
            checks.append(
                {
                    "check_id": "AADHAAR_KYC",
                    "status": "FAIL",
                    "reason": (
                        "Aadhaar KYC verification is pending"
                        if aadhaar_status == "PENDING"
                        else "Aadhaar KYC verification failed or is unavailable"
                    ),
                }
            )
            if aadhaar_status == "PENDING":
                reason_codes.append("KYC_AADHAAR_PENDING")
            else:
                reason_codes.append("KYC_AADHAAR_NOT_VERIFIED")

        # DOB remains required by this validator.
        if kyc.dob:
            checks.append(
                {
                    "check_id": "DOB",
                    "status": "PASS",
                    "reason": "Date of birth available",
                }
            )
        else:
            checks.append(
                {
                    "check_id": "DOB",
                    "status": "FAIL",
                    "reason": "Date of birth missing",
                }
            )
            reason_codes.append("KYC_DOB_MISSING")
    
        return KYCCheckResult(
            status = "PASS" if not reason_codes else "FAIL",
            checks = checks,
            reason_codes = reason_codes,
        )
        
kyc_validator = KYCValidator()