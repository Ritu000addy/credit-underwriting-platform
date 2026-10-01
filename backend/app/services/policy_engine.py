from datetime import date

from backend.app.schemas.application import ApplicationCreate
from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.policy import (PolicyEvaluationResult, PolicyRuleResult)

from backend.app.services.policy_config import POLICY_CONFIG

class PolicyEngine:

    def calculate_age(self, dob: date) -> int:

        today = date.today()

        age = (
            today.year
            - dob.year
            - (
                (today.month, today.day)
                < (dob.month, dob.day)
            )
        )

        return age

    def evaluate(
        self,
        application: ApplicationCreate,
        borrower: Borrower360,
        foir=None,
    ) -> PolicyEvaluationResult:
    
        rules: list[PolicyRuleResult] = []

        # AGE

        age_config = POLICY_CONFIG["age"]

        dob = borrower.kyc.dob

        if (
            age_config["min_age"] is None
            or age_config["max_age"] is None
        ):
            rules.append(
                PolicyRuleResult(
                    rule_id="AGE",
                    status="NOT_EVALUATED",
                    reason="Age policy parameters not configured",
                )
            )
        elif dob is None:
            rules.append(
                PolicyRuleResult(
                    rule_id="AGE",
                    status="NOT_EVALUATED",
                    reason="Date of birth not available",
                )
            )
        else:
            age = self.calculate_age(dob)
            
            if (
                age_config["min_age"]
                <= age
                <= age_config["max_age"]
            ):

                rules.append(
                    PolicyRuleResult(
                        rule_id="AGE",
                        status="PASS",
                        reason=(
                            f"Applicant age {age} is within "
                            f"the permitted range"
                        ),
                    )
                )

            else:
                rules.append(
                    PolicyRuleResult(
                        rule_id="AGE",
                        status="FAIL",
                        reason=(
                            f"Applicant age {age} is outside "
                            f"the permitted range"
                        ),
                    )
                )

        # INCOME / EMPLOYMENT / BUSINESS

        income_config = POLICY_CONFIG["income"]

        salary = borrower.employment_business.salary

        if income_config["minimum_income"] is None:

            rules.append(
                PolicyRuleResult(
                    rule_id="INCOME_ELIGIBILITY",
                    status="NOT_EVALUATED",
                    reason="Income eligibility parameters not configured",
                )
            )

        elif salary is None:
            rules.append(
                PolicyRuleResult(
                    rule_id="INCOME_ELIGIBILITY",
                    status="NOT_EVALUATED",
                    reason="Income information not available",
                )
            )

        elif salary >= income_config["minimum_income"]:

            rules.append(
                PolicyRuleResult(
                    rule_id="INCOME_ELIGIBILITY",
                    status="PASS",
                    reason=(
                        f"Monthly income {salary} meets "
                        f"minimum income requirement"
                    ),
                )
            )

        else:
            rules.append(
                PolicyRuleResult(
                    rule_id="INCOME_ELIGIBILITY",
                    status="FAIL",
                    reason=(
                        f"Monthly income {salary} is below "
                        f"minimum income requirement"
                    ),
                )
            )

        # GEOGRAPHY /SERVICEABLE AREA

        geography_config = POLICY_CONFIG["geography"]

        address = borrower.kyc.address

        serviceable_states = geography_config["serviceable_states"]
        serviceable_cities = geography_config["serviceable_cities"]
        serviceable_pincodes = geography_config["serviceable_pincodes"]

        if not (
            serviceable_states
            or serviceable_cities
            or serviceable_pincodes
        ):
            rules.append(
                PolicyRuleResult(
                    rule_id="GEOGRAPHY",
                    status="NOT_EVALUATED",
                    reason="Serviceable-area parameters not configured",
                )
            )
        elif not address:
            rules.append(
                PolicyRuleResult(
                    rule_id="GEOGRAPHY",
                    status="NOT_EVALUATED",
                    reason="Applicant address not available",
                )
            )

        else:

            address_text = address.lower()

            state_match = any(
                state.lower() in address_text
                for state in serviceable_states
            )

            city_match = any(
                city.lower() in address_text
                for city in serviceable_cities
            )

            pincode_match = any(
                str(pincode) in address_text
                for pincode in serviceable_pincodes
            )

            if state_match or city_match or pincode_match:

                rules.append(
                    PolicyRuleResult(
                        rule_id="GEOGRAPHY",
                        status="PASS",
                        reason="Applicant location is within serviceable area",
                    )
                )

            else:

                rules.append(
                    PolicyRuleResult(
                        rule_id="GEOGRAPHY",
                        status="FAIL",
                        reason="Applicant location is outside serviceable area",
                    )
                )

        # CREDIT BUREAU

        bureau_config = POLICY_CONFIG["bureau"]

        bureau_score = borrower.credit_bureau.score

        if bureau_config["minimum_score"] is None:
            rules.append(
                PolicyRuleResult(
                    rule_id="BUREAU",
                    status="NOT_EVALUATED",
                    reason="Bureau policy parameters not configured",
                )
            )
        elif bureau_score is None:

            rules.append(
                PolicyRuleResult(
                    rule_id="BUREAU",
                    status="NOT_EVALUATED",
                    reason="Bureau score not available",
                )
            )
        elif bureau_score >= bureau_config["minimum_score"]:

            rules.append(
                PolicyRuleResult(
                    rule_id="BUREAU",
                    status="PASS",
                    reason=(
                        f"Bureau score {bureau_score} meets "
                        f"minimum requirement"
                    ),
                )
            )
        else:

            rules.append(
                PolicyRuleResult(
                    rule_id="BUREAU",
                    status="FAIL",
                    reason=(
                        f"Bureau score {bureau_score} is below "
                        f"minimum requirement"
                    ),
                )
            )

        # EXISTING OBLIGATION / EXPOSURE

        exposure_config = POLICY_CONFIG["exposure"]

        total_outstanding = borrower.credit_bureau.total_outstanding

        if exposure_config["maximum_exposure"] is None:
            rules.append(
                PolicyRuleResult(
                    rule_id="EXPOSURE",
                    status="NOT_EVALUATED",
                    reason="Exposure limits not configured",
                )
            )
        elif total_outstanding is None:

            rules.append(
                PolicyRuleResult(
                    rule_id="EXPOSURE",
                    status="NOT_EVALUATED",
                    reason="Outstanding exposure not available",
                )
            )

        elif (
            total_outstanding
            <= exposure_config["maximum_exposure"]
        ):

            rules.append(
                PolicyRuleResult(
                    rule_id="EXPOSURE",
                    status="PASS",
                    reason=(
                        f"Existing exposure {total_outstanding} "
                        f"is within permitted limit"
                    ),
                )
            )
        else:

            rules.append(
                PolicyRuleResult(
                    rule_id="EXPOSURE",
                    status="FAIL",
                    reason=(
                        f"Existing exposure {total_outstanding} "
                        f"exceeds permitted limit"
                    ),
                )
            )

        # FOIR /DTI

        foir_config = POLICY_CONFIG["foir"]

        if foir_config["maximum_foir"] is None:
            rules.append(
                PolicyRuleResult(
                    rule_id="FOIR_DTI",
                    status="NOT_EVALUATED",
                    reason="FOIR/DTI parameters not configured",
                )
            )
        elif foir is None:
            rules.append(
                PolicyRuleResult(
                    rule_id="FOIR_DTI",
                    status="NOT_EVALUATED",
                    reason="FOIR could not be calculated",
                )
            )
        elif foir <= foir_config["maximum_foir"]:
            rules.append(
                PolicyRuleResult(
            rule_id="FOIR_DTI",
            status="PASS",
            reason=(
                f"FOIR {foir}% is within permitted limit"
            ),
        )
    )

        else:
            rules.append(
        PolicyRuleResult(
            rule_id="FOIR_DTI",
            status="FAIL",
            reason=(
                f"FOIR {foir}% exceeds permitted limit"
            ),
        )
    )     
        
        # VINTAGE / REPAYMENT BEHAVIOR

        vintage_config = POLICY_CONFIG["vintage"]

        minimum_vintage = vintage_config["minimum_vintage"]

        past_loans = borrower.internal_history.past_loans
        repayment_history = borrower.internal_history.repayment
        dpd_history = borrower.internal_history.dpd
        collection_history = borrower.internal_history.collections

        if minimum_vintage is None:
            rules.append(
                PolicyRuleResult(
                    rule_id="VINTAGE_REPAYMENT",
                    status="NOT_EVALUATED",
                    reason="Vintage and repayment parameters not configured",
                )
            )
        elif not past_loans:
            rules.append(
                PolicyRuleResult(
                    rule_id="VINTAGE_REPAYMENT",
                    status="NOT_EVALUATED",
                    reason="Past loan history  not available",
                )
            )
        else:
            repayment_issues = (
                bool(dpd_history)
                or bool(collection_history)
            )

            if repayment_issues:
                rules.append(
                    PolicyRuleResult(
                        rule_id="VINTAGE_REPAYMENT",
                        status="FAIL",
                        reason="Adverse repayment or collection history identified",
                    )
                )

            elif repayment_history:
                rules.append(
                    PolicyRuleResult(
                        rule_id="VINTAGE_REPAYMENT",
                        status="PASS",
                        reason="Past loan and repayment history available with no adverse DPD or collection records",
                    )
                )
            else:
                rules.append(
                    PolicyRuleResult(
                        rule_id="VINTAGE_REPAYMENT",
                        status="NOT_EVALUATED",
                        reason="Repayment history not available",
                    )
                )

        # KYC / BANK ACCOUNT VALIDATION

        kyc = borrower.kyc
        if (
            kyc.pan
            and kyc.ekyc_result == "VERIFIED"
        ):
            rules.append(
                PolicyRuleResult(
                    rule_id="KYC_BANK_VALIDATION",
                    status="PASS",
                    reason="KYC validation passed",
                )
            )
        else:

            rules.append(
                PolicyRuleResult(
                    rule_id="KYC_BANK_VALIDATION",
                    status="FAIL",
                    reason="KYC validation requirements not satisfied",
                )
            )

        # LOAN AMOUNT / TENURE

        loan_config = POLICY_CONFIG["loan"]

        amount_valid = (
            application.requested_amount
            >= loan_config["minimum_amount"]
            and
            application.requested_amount
            <= loan_config["maximum_amount"]
        )

        tenure_valid = (
            application.loan_tenure_months
            >= loan_config["minimum_tenure_months"]
            and
            application.loan_tenure_months
            <= loan_config["maximum_tenure_months"]
        )

        if amount_valid and tenure_valid:

            rules.append(
                PolicyRuleResult(
                    rule_id="LOAN_AMOUNT_TENURE",
                    status="PASS",
                    reason=(
                        "Requested loan amount and tenure "
                        "are within permitted limits"
                    ),
                )
            )

        else:
            rules.append(
                PolicyRuleResult(
                    rule_id="LOAN_AMOUNT_TENURE",
                    status="FAIL",
                    reason=(
                        "Requested loan amount or tenure "
                        "is outside permitted limits"
                    ),
                )
            )

        # POLICY EXCEPTION
        
        exception_config = POLICY_CONFIG["exceptions"]

        if not exception_config["enabled"]:
            rules.append(
                PolicyRuleResult(
                    rule_id="POLICY_EXCEPTION",
                    status="NOT_EVALUATED",
                    reason="Policy exception rules not enabled",
                )
            )

        elif not exception_config["rules"]:
            rules.append(
                PolicyRuleResult(
                    rule_id="POLICY_EXCEPTION",
                    status="NOT_EVALUATED",
                    reason="Policy exception rules not configured",
                )
            )
        else:
            rules.append(
                PolicyRuleResult(
                    rule_id="POLICY_EXCEPTION",
                    status="NOT_EVALUATED",
                    reason="Policy exception evaluation not implemented",
                )
            )

        # OVERALL POLICY STATUS

        has_fail = any(
            rule.status == "FAIL"
            for rule in rules
        )

        has_not_evaluated = any(
            rule.status == "NOT_EVALUATED"
            for rule in rules
        )

        if has_fail:

            policy_status = "REJECT"

        elif has_not_evaluated:

            policy_status = "REFER"

        else:
            policy_status = "APPROVE"

        return PolicyEvaluationResult(
            policy_status=policy_status,
            rules=rules,
        )

policy_engine= PolicyEngine()