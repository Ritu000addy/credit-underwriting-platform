from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.genai_underwriting import GenAIUnderwritingResult
from backend.app.schemas.underwriting import UnderwritingResult

from backend.app.services.genai_provider import genai_provider


class GenAIUnderwritingService:

    def generate(
        self,
        borrower: Borrower360,
        underwriting: UnderwritingResult,
    ) -> GenAIUnderwritingResult:

        # ---------------------------------------------------------
        # Underwriting data consistency validation
        # ---------------------------------------------------------

        if (
            borrower.credit_bureau
            and borrower.credit_bureau.score is not None
            and underwriting.risk_assessment
            and underwriting.risk_assessment.credit_score is not None
            and borrower.credit_bureau.score
            != underwriting.risk_assessment.credit_score
        ):
            raise ValueError(
                "UNDERWRITING_DATA_INCONSISTENT: "
                "Credit score does not match borrower bureau data."
            )

        if (
            underwriting.risk_assessment
            and underwriting.risk_assessment.credit_score is not None
            and underwriting.decision
            and underwriting.decision.credit_score is not None
            and underwriting.risk_assessment.credit_score
            != underwriting.decision.credit_score
        ):
            raise ValueError(
                "UNDERWRITING_DATA_INCONSISTENT: "
                "Credit score does not match the underwriting decision."
            )

        if (
            underwriting.decision
            and underwriting.application_id
            != underwriting.decision.application_id
        ):
            raise ValueError(
                "UNDERWRITING_DATA_INCONSISTENT: "
                "Application ID does not match the credit decision."
            )

        if underwriting.risk_assessment and underwriting.decision:

            risk = underwriting.risk_assessment
            decision = underwriting.decision

            consistency_fields = [
                "risk_grade",
                "probability_of_default",
                "affordability_score",
                "repayment_propensity",
                "fraud_score",
                "fraud_risk_level",
                "fraud_confidence",
                "income_stability_score",
                "income_trend",
                "risk_segment",
                "recommended_amount",
                "recommended_tenure",
                "recommended_emi",
                "foir",
                "confidence",
                "model_version",
            ]

            for field_name in consistency_fields:
                risk_value = getattr(risk, field_name)
                decision_value = getattr(decision, field_name)

                if (
                    risk_value is not None
                    and decision_value is not None
                    and risk_value != decision_value
                ):
                    raise ValueError(
                        "UNDERWRITING_DATA_INCONSISTENT: "
                        f"{field_name} does not match between "
                        "risk assessment and credit decision."
                    )

            if risk.fraud_reason_codes != decision.fraud_reason_codes:
                raise ValueError(
                    "UNDERWRITING_DATA_INCONSISTENT: "
                    "Fraud reason codes do not match between "
                    "risk assessment and credit decision."
                )

            if risk.reason_codes != decision.reason_codes:
                raise ValueError(
                    "UNDERWRITING_DATA_INCONSISTENT: "
                    "Reason codes do not match between "
                    "risk assessment and credit decision."
                )

        strengths: list[str] = []
        concerns: list[str] = []
        missing_information: list[str] = []
        policy_exceptions: list[str] = []

        # ---------------------------------------------------------
        # Borrower summary
        # ---------------------------------------------------------

        borrower_summary_parts: list[str] = []

        if borrower.kyc:
            if borrower.kyc.pan:
                borrower_summary_parts.append("PAN information available")

            if borrower.kyc.dob:
                borrower_summary_parts.append("Date of birth available")

            if borrower.kyc.aadhaar_kyc_status:
                borrower_summary_parts.append(
                    f"Aadhaar KYC status: {borrower.kyc.aadhaar_kyc_status}"
                )

        if borrower.credit_bureau:
            if borrower.credit_bureau.score is not None:
                borrower_summary_parts.append(
                    f"Bureau score: {borrower.credit_bureau.score}"
                )

            if borrower.credit_bureau.dpd is not None:
                borrower_summary_parts.append(
                    f"Bureau DPD: {borrower.credit_bureau.dpd}"
                )

        borrower_summary = "; ".join(borrower_summary_parts)

        # ---------------------------------------------------------
        # Financial summary
        # ---------------------------------------------------------

        financial_summary_parts: list[str] = []

        if borrower.bank_cash_flow:
            bank = borrower.bank_cash_flow

            if bank.credits is not None:
                financial_summary_parts.append(
                    f"Bank credits: {bank.credits}"
                )

            if bank.debits is not None:
                financial_summary_parts.append(
                    f"Bank debits: {bank.debits}"
                )

            if bank.balance is not None:
                financial_summary_parts.append(
                    f"Average balance: {bank.balance}"
                )

            if bank.emi is not None:
                financial_summary_parts.append(
                    f"Existing EMI: {bank.emi}"
                )

            if bank.bounce is not None:
                financial_summary_parts.append(
                    f"Bank bounce count: {bank.bounce}"
                )

        if borrower.employment_business:
            employment = borrower.employment_business

            if employment.salary is not None:
                financial_summary_parts.append(
                    f"Reported salary/income: {employment.salary}"
                )

            if employment.employer:
                financial_summary_parts.append(
                    f"Employer: {employment.employer}"
                )

        financial_summary = "; ".join(financial_summary_parts)

        # ---------------------------------------------------------
        # Strengths
        # ---------------------------------------------------------

        if borrower.credit_bureau:
            if (
                borrower.credit_bureau.score is not None
                and borrower.credit_bureau.score >= 700
            ):
                strengths.append(
                    "Bureau score is above the development reference threshold."
                )

            if borrower.credit_bureau.dpd == 0:
                strengths.append(
                    "No current bureau DPD reported."
                )

            if borrower.credit_bureau.write_offs == 0:
                strengths.append(
                    "No bureau write-offs reported."
                )

        if borrower.bank_cash_flow:
            if borrower.bank_cash_flow.bounce == 0:
                strengths.append(
                    "No bank payment bounces reported."
                )

            if borrower.bank_cash_flow.income_pattern:
                income_trend = borrower.bank_cash_flow.income_pattern.get(
                    "income_trend"
                )

                if income_trend == "STABLE":
                    strengths.append(
                        "Income trend is reported as stable."
                    )

        if borrower.kyc:
            if borrower.kyc.aadhaar_kyc_status == "VERIFIED":
                strengths.append(
                    "Aadhaar KYC verification completed."
                )

        # ---------------------------------------------------------
        # Concerns
        # ---------------------------------------------------------

        if borrower.credit_bureau:
            if (
                borrower.credit_bureau.enquiries is not None
                and borrower.credit_bureau.enquiries > 3
            ):
                concerns.append(
                    "Multiple recent credit enquiries reported."
                )

        if borrower.bank_cash_flow:
            if borrower.bank_cash_flow.bounce is not None:
                if borrower.bank_cash_flow.bounce > 0:
                    concerns.append(
                        "Bank payment bounces reported."
                    )

        if borrower.kyc:
            if borrower.kyc.aadhaar_kyc_status != "VERIFIED":
                concerns.append(
                    "Aadhaar KYC is not currently verified."
                )

        # ---------------------------------------------------------
        # Underwriting result analysis
        # ---------------------------------------------------------

        if underwriting.completeness:
            if underwriting.completeness.status != "COMPLETE":
                missing_information.extend(
                    underwriting.completeness.missing_fields
                )

        if underwriting.kyc:
            if underwriting.kyc.reason_codes:
                concerns.extend(
                    underwriting.kyc.reason_codes
                )

        if underwriting.policy:
            for rule in underwriting.policy.rules:

                if rule.status == "NOT_EVALUATED":
                    policy_exceptions.append(
                        f"{rule.rule_id}: {rule.reason}"
                    )

                    missing_information.append(
                        rule.reason
                    )

        # ---------------------------------------------------------
        # Credit narrative
        # ---------------------------------------------------------

        decision = None

        if underwriting.decision:
            decision = underwriting.decision.decision

        credit_narrative_parts = []

        if decision:
            credit_narrative_parts.append(
                f"Current underwriting decision is {decision}."
            )

        if underwriting.risk_assessment:
            risk = underwriting.risk_assessment

            if risk.credit_score is not None:
                credit_narrative_parts.append(
                    f"Credit score is {risk.credit_score}."
                )

            if risk.risk_grade:
                credit_narrative_parts.append(
                    f"Development risk grade is {risk.risk_grade}."
                )

            if risk.probability_of_default is not None:
                credit_narrative_parts.append(
                    f"Estimated probability of default is "
                    f"{risk.probability_of_default}."
                )

            if risk.foir is not None:
                credit_narrative_parts.append(
                    f"FOIR is {risk.foir}%."
                )

        if policy_exceptions:
            credit_narrative_parts.append(
                "Some policy parameters require configuration or review "
                "before a fully policy-driven decision can be made."
            )

        credit_narrative = " ".join(credit_narrative_parts)

        # ---------------------------------------------------------
        # Officer summary
        # ---------------------------------------------------------

        officer_summary_parts = []

        if strengths:
            officer_summary_parts.append(
                "Strengths: " + "; ".join(strengths)
            )

        if concerns:
            officer_summary_parts.append(
                "Concerns: " + "; ".join(concerns)
            )

        if policy_exceptions:
            officer_summary_parts.append(
                "Policy items requiring attention: "
                + "; ".join(policy_exceptions)
            )

        officer_summary = " ".join(officer_summary_parts)

        provider_status = (
            "CONFIGURED"
            if genai_provider.is_configured()
            else "NOT_CONFIGURED"
        )

        return GenAIUnderwritingResult(
            status="COMPLETED",
            borrower_summary=borrower_summary or None,
            financial_summary=financial_summary or None,
            credit_narrative=credit_narrative or None,
            strengths=strengths,
            concerns=concerns,
            missing_information=missing_information,
            policy_exceptions=policy_exceptions,
            officer_summary=officer_summary or None,
            model_name=f"DEV-RULE-BASED-GENAI ({provider_status})",
            model_version="0.1",
        )


genai_underwriting_service = GenAIUnderwritingService()