from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.kyc import KYCCheckResult

class KYCValidator:

    def validate(
        self,
        borrower: Borrower360,
    ) -> KYCCheckResult:

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
        
        # PAN availability
        if kyc.pan:
            checks.append(
                {
                    "check_id": "PAN",
                    "status": "PASS",
                    "reason": "PAN information available",
                }
            )
        else:
            checks.append(
                {
                    "check_id": "PAN",
                    "status": "FAIL",
                    "reason": "PAN information missing",
                }
            )
            reason_codes.append("KYC_PAN_MISSING")
        
        # e-KYC status
        if kyc.ekyc_result:
            checks.append(
                {
                    "check_id": "EKYC",
                    "status": "PASS",
                    "reason": "e-KYC result available",
                }
            )
        else:
            checks.append(
                {
                    "check_id": "EKYC",
                    "status": "FAIL",
                    "reason": "e-KYC result missing",
                }
            )
            reason_codes.append("KYC_EKYC_MISSING")

        # Aadhaar KYC status
        if kyc.aadhaar_kyc_status == "VERIFIED":
            checks.append(
                {
                    "check_id": "AADHAAR_KYC",
                    "status": "PASS",
                    "reason": "Aadhaar KYC verification passed",
                }
            )
        elif kyc.aadhaar_kyc_status == "PENDING":
            checks.append(
                {
                    "check_id": "AADHAAR_KYC",
                    "status": "FAIL",
                    "reason": "Aadhaar KYC verification is pending",
                }
            )
            reason_codes.append("KYC_AADHAAR_PENDING")
        else:
            checks.append(
                {
                    "check_id": "AADHAAR_KYC",
                    "status": "FAIL",
                    "reason": "Aadhaar KYC verification failed or is unavailable",
                }
            )
            reason_codes.append("KYC_AADHAAR_NOT_VERIFIED")

        # DOB
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
    
        # overall result
        status = "PASS" if not reason_codes else "FAIL"

        return KYCCheckResult(
            status = status,
            checks = checks,
            reason_codes = reason_codes,
        )
        
kyc_validator = KYCValidator()