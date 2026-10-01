from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.bureau_history import BureauHistoryResult

class BureauHistoryValidator:
    def validate(
        self,
        borrower: Borrower360,
    ) -> BureauHistoryResult:

        bureau_checks: list[dict] = []
        internal_history_checks: list[dict] = []
        reason_codes: list[str] = []

        # Credit Bureau

        bureau = borrower.credit_bureau

        if bureau is None:
            return BureauHistoryResult(
                status="FAIL",
                bureau_checks=[
                    {
                        "check_id": "BUREAU_DATA",
                        "status": "FAIL",
                        "reason": "Credit bureau data not available",
                    }
                ],
                internal_history_checks=[],
                reason_codes=["BUREAU_DATA_MISSING"],
            )
        
        if bureau.score is not None:
            bureau_checks.append(
                {
                    "check_id": "BUREAU_SCORE",
                    "status": "PASS",
                    "reason": "Bureau score available",
                }
            )
        else:
            bureau_checks.append(
                {
                    "check_id": "BUREAU_SCORE",
                    "status": "FAIL",
                    "reason": "Bureau score missing",
                }
            )
            reason_codes.append("BUREAU_SCORE_MISSING")
        
        # DPD
        if bureau.dpd is not None:
            bureau_checks.append(
                {
                    "check_id": "DPD",
                    "status": "PASS",
                    "reason": "Bureau DPD information available",
                }
            )
        else:
            bureau_checks.append(
                {
                    "check_id": "DPD",
                    "status": "FAIL",
                    "reason": "Bureau DPD information missing",
                }
            )
            reason_codes.append("BUREAU_DPD_MISSING")
        
        # Enquiries
        if bureau.enquiries is not None:
            bureau_checks.append(
                {
                    "check_id": "ENQUIRIES",
                    "status": "PASS",
                    "reason": "Credit enquiry information available",
                }
            )
        else:
            bureau_checks.append(
                {
                    "check_id": "ENQUIRIES",
                    "status": "FAIL",
                    "reason": "Credit enquiry information missing",
                }
            )
            reason_codes.append("BUREAU_ENQUIRIES_MISSING")
        
        # Active loans
        if bureau.active_loans is not None:
            bureau_checks.append(
                {
                    "check_id": "ACTIVE_LOANS",
                    "status": "PASS",
                    "reason": "Active loan information available",
                }
            )
        else:
            bureau_checks.append(
                {
                    "check_id": "ACTIVE_LOANS",
                    "status": "FAIL",
                    "reason": "Active loan information missing",
                }
            )
            reason_codes.append("BUREAU_ACTIVE_LOANS_MISSING")
        
        # Write offs
        if bureau.write_offs is not None:
            bureau_checks.append(
                {
                    "check_id": "WRITE_OFFS",
                    "status": "PASS",
                    "reason": "Write-off information available",
                }
            )
        else:
            bureau_checks.append(
                {
                    "check_id": "WRITE_OFFS",
                    "status": "FAIL",
                    "reason": "Write-off information missing",
                }
            )
            reason_codes.append("BUREAU_WRITE_OFFS_MISSING")
        

        # Internal History

        internal_history = borrower.internal_history
        
        if internal_history is None:
            internal_history_checks.append(
                {
                    "check_id": "INTERNAL_HISTORY",
                    "status": "FAIL",
                    "reason": "Internal customer history not available",
                }
            )
            reason_codes.append("INTERNAL_HISTORY_MISSING")

        else:
            if internal_history.past_loans:
                internal_history_checks.append(
                    {
                        "check_id": "PAST_LOANS",
                        "status": "AVAILABLE",
                        "reason": "Past loan information available",
                    }
                )
            else:
                internal_history_checks.append(
                    {
                        "check_id": "PAST_LOANS",
                        "status": "NOT_AVAILABLE",
                        "reason": "No past loans recorded",
                    }
                )

            if internal_history.repayment:
                internal_history_checks.append(
                    {
                        "check_id": "REPAYMENT_HISTORY",
                        "status": "AVAILABLE",
                        "reason": "Repayment history available",
                    }
                )
            else:
                internal_history_checks.append(
                    {
                        "check_id": "REPAYMENT_HISTORY",
                        "status": "NOT_AVAILABLE",
                        "reason": "No internal repayment history recorded",
                    }
                )

            if internal_history.dpd:
                internal_history_checks.append(
                    {
                        "check_id": "INTERNAL_DPD",
                        "status": "AVAILABLE",
                        "reason": "Internal DPD information available",
                    }
                )
            else:
                internal_history_checks.append(
                    {
                        "check_id": "INTERNAL_DPD",
                        "status": "NOT_AVAILABLE",
                        "reason": "No internal DPD history recorded",
                    }
                )

            if internal_history.collections:
                internal_history_checks.append(
                    {
                        "check_id": "COLLECTIONS",
                        "status": "AVAILABLE",
                        "reason": "Collections history available",
                    }
                )
            else:
                internal_history_checks.append(
                    {
                        "check_id": "COLLECTIONS",
                        "status": "NOT_AVAILABLE",
                        "reason": "No internal collections history recorded",
                    }
                )

        status = "PASS" if not reason_codes else "FAIL"

        return BureauHistoryResult(
            status=status,
            bureau_checks=bureau_checks,
            internal_history_checks=internal_history_checks,
            reason_codes=reason_codes,
        )
            
bureau_history_validator = BureauHistoryValidator()