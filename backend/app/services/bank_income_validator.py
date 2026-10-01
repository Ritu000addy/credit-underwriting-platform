from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.bank_income import BankIncomeResult

class BankIncomeValidator:
    def validate(
        self,
        borrower: Borrower360,
    ) -> BankIncomeResult:

        bank_cash_flow_checks: list[str] = []
        employment_business_checks: list[str] = []
        reason_codes: list[str]=[]

        # Bank/ Cash Flow

        bank = borrower.bank_cash_flow

        if bank is None:
            return BankIncomeResult(
                status="FAIL",
                bank_cash_flow_checks=[
                    {
                        "check_id": "BANK_DATA",
                        "status": "FAIL",
                        "reason": "Bank/cash flow data not available",
                    }
                ],
                employment_business_checks=[],
                reason_codes=["BANK_DATA_MISSING"],
            )

        if bank.credits is not None:
            bank_cash_flow_checks.append(
                {
                    "check_id": "CREDITS",
                    "status": "AVAILABLE",
                    "reason": "Bank credit information available",
                }
            )
        else:
            bank_cash_flow_checks.append(
                {
                    "check_id": "CREDITS",
                    "status": "NOT_AVAILABLE",
                    "reason": "Bank credit information not available",
                }
            )
            reason_codes.append("BANK_CREDITS_MISSING")

        if bank.debits is not None:
            bank_cash_flow_checks.append(
                {
                    "check_id": "DEBITS",
                    "status": "AVAILABLE",
                    "reason": "Bank debit information available",
                }
            )
        else:
            bank_cash_flow_checks.append(
                {
                    "check_id": "DEBITS",
                    "status": "NOT_AVAILABLE",
                    "reason": "Bank debit information not available",
                }
            )
            reason_codes.append("BANK_DEBITS_MISSING")

        if bank.balance is not None:
            bank_cash_flow_checks.append(
                {
                    "check_id": "BALANCE",
                    "status": "AVAILABLE",
                    "reason": "Bank balance information available",
                }
            )
        else:
            bank_cash_flow_checks.append(
                {
                    "check_id": "BALANCE",
                    "status": "NOT_AVAILABLE",
                    "reason": "Bank balance information not available",
                }
            )
            reason_codes.append("BANK_BALANCE_MISSING")
        
        if bank.emi is not None:
            bank_cash_flow_checks.append(
                {
                    "check_id": "EMI",
                    "status": "AVAILABLE",
                    "reason": "Existing EMI information available",
                }
            )
        else:
            bank_cash_flow_checks.append(
                {
                    "check_id": "EMI",
                    "status": "NOT_AVAILABLE",
                    "reason": "Existing EMI information not available",
                }
            )
            reason_codes.append("BANK_EMI_MISSING")

        if bank.bounce is not None:
            bank_cash_flow_checks.append(
                {
                    "check_id": "BOUNCE",
                    "status": "AVAILABLE",
                    "reason": "Bank bounce information available",
                }
            )
        else:
            bank_cash_flow_checks.append(
                {
                    "check_id": "BOUNCE",
                    "status": "NOT_AVAILABLE",
                    "reason": "Bank bounce information not available",
                }
            )
            reason_codes.append("BANK_BOUNCE_MISSING")

        if bank.income_pattern is not None:
            bank_cash_flow_checks.append(
                {
                    "check_id": "INCOME_PATTERN",
                    "status": "AVAILABLE",
                    "reason": "Income pattern information available",
                }
            )
        else:
            bank_cash_flow_checks.append(
                {
                    "check_id": "INCOME_PATTERN",
                    "status": "NOT_AVAILABLE",
                    "reason": "Income pattern information not available",
                }
            )
            reason_codes.append("BANK_INCOME_PATTERN_MISSING")
        
        # Employment /Business

        employment = borrower.employment_business
        
        if employment is None:
            return BankIncomeResult(
                status="FAIL",
                bank_cash_flow_checks=bank_cash_flow_checks,
                employment_business_checks=[
                    {
                        "check_id": "EMPLOYMENT_BUSINESS_DATA",
                        "status": "FAIL",
                        "reason": "Employment/business data not available",
                    }
                ],
                reason_codes=reason_codes + [
                    "EMPLOYMENT_BUSINESS_DATA_MISSING"
                ],
            )

        if employment.salary is not None:
            employment_business_checks.append(
                {
                    "check_id": "SALARY",
                    "status": "AVAILABLE",
                    "reason": "Salary information available",
                }
            )
        else:
            employment_business_checks.append(
                {
                    "check_id": "SALARY",
                    "status": "NOT_AVAILABLE",
                    "reason": "Salary information not available",
                }
            )
        
        if employment.employer:
            employment_business_checks.append(
                {
                    "check_id": "EMPLOYER",
                    "status": "AVAILABLE",
                    "reason": "Employer information available",
                }
            )
        else:
            employment_business_checks.append(
                {
                    "check_id": "EMPLOYER",
                    "status": "NOT_AVAILABLE",
                    "reason": "Employer information not available",
                }
            )

        if employment.gst:
            employment_business_checks.append(
                {
                    "check_id": "GST",
                    "status": "AVAILABLE",
                    "reason": "GST information available",
                }
            )
        else:
            employment_business_checks.append(
                {
                    "check_id": "GST",
                    "status": "NOT_AVAILABLE",
                    "reason": "GST information not available",
                }
            )

        if employment.udyam:
            employment_business_checks.append(
                {
                    "check_id": "UDYAM",
                    "status": "AVAILABLE",
                    "reason": "Udyam information available",
                }
            )
        else:
            employment_business_checks.append(
                {
                    "check_id": "UDYAM",
                    "status": "NOT_AVAILABLE",
                    "reason": "Udyam information not available",
                }
            )

        if employment.business_vintage is not None:
            employment_business_checks.append(
                {
                    "check_id": "BUSINESS_VINTAGE",
                    "status": "AVAILABLE",
                    "reason": "Business vintage information available",
                }
            )
        else:
            employment_business_checks.append(
                {
                    "check_id": "BUSINESS_VINTAGE",
                    "status": "NOT_AVAILABLE",
                    "reason": "Business vintage information not available",
                }
            )

        status = "PASS" if not reason_codes else "FAIL"

        return BankIncomeResult(
            status=status,
            bank_cash_flow_checks=bank_cash_flow_checks,
            employment_business_checks=employment_business_checks,
            reason_codes=reason_codes,
        )

bank_income_validator = BankIncomeValidator()