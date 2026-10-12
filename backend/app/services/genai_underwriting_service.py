import json
import time
import logging

from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.genai_underwriting import GenAIUnderwritingResult
from backend.app.schemas.genai_llm import GenAILLMResponse
from backend.app.schemas.genai_evidence import GenAIEvidence
from backend.app.schemas.underwriting import UnderwritingResult

from backend.app.services.genai_provider import genai_provider


class GenAIUnderwritingService:

    # Public service
    def generate(
        self,
        borrower: Borrower360,
        underwriting: UnderwritingResult,
    ) -> GenAIUnderwritingResult:

        # ---------------------------------------------------------
        # Underwriting data consistency validation
        # ---------------------------------------------------------

        self._validate_consistency(
            borrower=borrower,
            underwriting=underwriting,
        )

        # Exisiting deterministic analysis
        strengths: list[str] = []
        concerns: list[str] = []
        missing_information: list[str] = []
        policy_exceptions: list[str] = []

        borrower_summary= self._build_borrower_summary(
            borrower
        )
        financial_summary = self._build_financial_summary(
            borrower
        )

        # Strengths
        
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

                income_trend = (
                    borrower.bank_cash_flow.income_pattern.get(
                        "income_trend"
                    )
                )

                if income_trend == "STABLE":
                    strengths.append(
                        "income trend is reported as stable."
                    )

        if borrower.kyc:

            if (
                borrower.kyc.aadhaar_kyc_status == "VERIFIED"
            ):
                strengths.append(
                    "Aadhaar KYC verification completed."
                )

        # Concerns

        if borrower.credit_bureau:

            if (
                borrower.credit_bureau.enquiries is not None
                and borrower.credit_bureau.enquiries > 3
            ):

                concerns.append(
                    "Multiple recent credit enquiries reported."
                )

        if borrower.bank_cash_flow:

            if (
                borrower.bank_cash_flow.bounce is not None
                and borrower.bank_cash_flow.bounce > 0
            ):

                concerns.append(
                    "Bank payment bounces reported."
                )

        if borrower.kyc:

            if (
                borrower.kyc.aadhaar_kyc_status != "VERIFIED"
            ):

                concerns.append(
                    "Aadhaar KYC is not currently verified."
                )

        # Underwriting result analysis

        if underwriting.completeness:

            if underwriting.completeness.status != "COMPLETE":

                missing_information.extend(
                    underwriting.completeness.missing_fields
                )

        if underwriting.kyc:
            if underwriting.kyc.status != "PASS":
                if underwriting.kyc.reason_codes:
                    concerns.extend(
                        underwriting.kyc.reason_codes
                    )
                else:
                    concerns.append(
                        "KYC verification requires review."
                    )

                # Risk assessment concerns

        if underwriting.risk_assessment:
            risk = underwriting.risk_assessment

            risk_reason_codes = set(
                risk.reason_codes or []
            )

            if "WEAK_REPAYMENT_HISTORY" in risk_reason_codes:
                concerns.append(
                    "Repayment history is flagged as weak by the risk assessment."
                )

            if risk.risk_segment == "HIGH_RISK":
                concerns.append(
                    "The risk assessment classifies this application as HIGH_RISK."
                )

            if "POLICY_DATA_INCOMPLETE" in risk_reason_codes:
                policy_data_concern = (
                    "The risk assessment flags incomplete policy data; "
                    "verify the applicable policy checks before final credit approval."
                )

                if policy_data_concern not in concerns:
                    concerns.append(policy_data_concern)

                policy_exception = (
                    "POLICY_DATA_INCOMPLETE: "
                    "Applicable policy data or checks require verification."
                )

                if policy_exception not in policy_exceptions:
                    policy_exceptions.append(policy_exception)

        if underwriting.policy:

            for rule in underwriting.policy.rules:

                if rule.status == "NOT_EVALUATED":

                    policy_exceptions.append(
                        f"{rule.rule_id}: {rule.reason}"
                    )

                    missing_information.append(
                        rule.reason
                    )

        # Deterministic credit narrative

        credit_narrative = (
            self._build_credit_narrative(
                underwriting = underwriting,
                policy_exceptions = policy_exceptions,
            )
        )
        
        # Deterministic officer summary

        officer_summary = (
            self._build_officer_summary(
                strengths = strengths,
                concerns = concerns,
                policy_exceptions = policy_exceptions,                
            )
        )

        # Build controlled evidence for the LLM

        evidence = self._build_llm_evidence(
            borrower=borrower,
            underwriting=underwriting,
            strengths = strengths,
            concerns = concerns,
            missing_information = missing_information,
            policy_exceptions = policy_exceptions,
        )
        
        # If LLM is not configured, retain deterministic behaviour

        if not genai_provider.is_configured():

            return GenAIUnderwritingResult(
                status = "COMPLETED",
                borrower_summary= borrower_summary or None,
                financial_summary= financial_summary or None,
                credit_narrative= credit_narrative or None,
                strengths = strengths,
                concerns = concerns,
                missing_information = missing_information,
                policy_exceptions = policy_exceptions,
                officer_summary= officer_summary or None,
                model_name= "DEV-RULE-BASED-GENAI (NOT_CONFIGURED)",
                model_version= "0.1",
            )

        # Actual LLM generation

        prompt = self._build_llm_prompt(
            evidence = evidence.model_dump()
        )

        llm_started_at = time.perf_counter()

        try:
            raw_response = genai_provider.generate(
                prompt
            )

            llm_duration_seconds = time.perf_counter() - llm_started_at
            logging.info(
                "GenAI provider generation completed in %.2f seconds",
                llm_duration_seconds,
            )

        except Exception:
            logging.exception("GenAI generation failed")
            raise RuntimeError("GENAI_GENERATION_FAILED") from None

        # Parse and validate LLM response

        try:
            llm_result = self._parse_llm_response(
                raw_response
            )

        except Exception as exc:
            raise RuntimeError(
                "GENAI_INVALID_STRUCTURED_RESPONSE"
            ) from exc

        # Return controlled LLM result

        return GenAIUnderwritingResult(
            status="COMPLETED",

            borrower_summary= (
                borrower_summary
                or None
            ),
            
            financial_summary=(               
                financial_summary
                or None
            ),

            credit_narrative= (
                credit_narrative
                or None
            ),

            strengths=strengths,
                

            concerns= concerns,


            missing_information= 
                missing_information,
                

            policy_exceptions= 
                policy_exceptions,
                

            officer_summary= (
                officer_summary
                or None
            ),

            llm_analyst_narrative=self._validate_llm_narrative(
                narrative=llm_result.llm_analyst_narrative,
                underwriting=underwriting,
            ),

            model_name= (
                f"LLM-{genai_provider.provider}"
            ),

            model_version= (
                genai_provider.model
            ),
        )


    # Consistency validation

    def _validate_consistency(
        self,
        borrower: Borrower360,
        underwriting: UnderwritingResult,
    ) -> None:

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

        if (
            underwriting.risk_assessment
            and underwriting.decision
        ):

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

                risk_value = getattr(
                    risk,
                    field_name
                )

                decision_value = getattr(
                    decision,
                    field_name
                )

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

            if (
                risk.fraud_reason_codes 
                != decision.fraud_reason_codes
            ):
                raise ValueError(
                    "UNDERWRITING_DATA_INCONSISTENT: "
                    "Fraud reason codes do not match between "
                    "risk assessment and credit decision."
                )

            if (
                risk.reason_codes 
                != decision.reason_codes
            ):
                raise ValueError(
                    "UNDERWRITING_DATA_INCONSISTENT: "
                    "Reason codes do not match between "
                    "risk assessment and credit decision."
                )

    # Borrower summary

    def _build_borrower_summary(
        self,
        borrower: Borrower360,
    ) -> str:

        parts: list[str] = []

        if borrower.kyc:

            if borrower.kyc.pan:
                parts.append(
                    "PAN information available"
                )

            if borrower.kyc.dob:
                parts.append(
                    "Date of birth available"
                )

            if borrower.kyc.aadhaar_kyc_status:
                parts.append(
                    "Aadhaar KYC status:"
                    f"{borrower.kyc.aadhaar_kyc_status}"
                )

        if borrower.credit_bureau:

            if borrower.credit_bureau.score is not None:
                parts.append(
                    "Bureau score:"
                    f"{borrower.credit_bureau.score}"
                )

            if borrower.credit_bureau.dpd is not None:
                parts.append(
                    "Bureau DPD:"
                    f"{borrower.credit_bureau.dpd}"
                )

        return ";".join(parts)

        # Financial summary
    
    def _build_financial_summary(
        self,
        borrower: Borrower360,
    ) -> str:

        parts: list[str] = []

        if borrower.bank_cash_flow:

            bank = borrower.bank_cash_flow

            if bank.credits is not None:
                parts.append(
                    f"Bank credits: {bank.credits}"
                )

            if bank.debits is not None:
                parts.append(
                    f"Bank debits: {bank.debits}"
                )

            if bank.balance is not None:
                parts.append(
                    f"Average balance: {bank.balance}"
                )

            if bank.emi is not None:
                parts.append(
                    f"Existing EMI: {bank.emi}"
                )

            if bank.bounce is not None:
                parts.append(
                    f"Bank bounce count: {bank.bounce}"
                )

            if bank.transaction_count is not None:
                parts.append(
                    f"Transaction count: {bank.transaction_count}"
                )

            if bank.income_pattern:

                income_trend = bank.income_pattern.get(
                    "income_trend"
                )

                if income_trend:
                    parts.append(
                    f"Income trend: {income_trend}"
                )

        if borrower.employment_business:

            employment = borrower.employment_business

            if employment.salary is not None:
                parts.append(
                    "Reported salary/income: "
                    f"{employment.salary}"
                )

            if employment.employer:
                parts.append(
                    f"Employer: {employment.employer}"
                )

        return "; ".join(parts)

    # =========================================================
    # CREDIT NARRATIVE
    # =========================================================

    def _build_credit_narrative(
        self,
        underwriting: UnderwritingResult,
        policy_exceptions: list[str],
    ) -> str:

        parts: list[str] = []

        if underwriting.decision:

            decision = underwriting.decision.decision

            if decision:
                parts.append(
                    f"Current underwriting decision is {decision}."
                )

        if underwriting.risk_assessment:

            risk = underwriting.risk_assessment

            if risk.credit_score is not None:
                parts.append(
                    f"Credit score is {risk.credit_score}."
                )

            if risk.risk_grade:
                parts.append(
                    f"Development risk grade is {risk.risk_grade}."
                )

            if risk.probability_of_default is not None:
                parts.append(
                    "Estimated probability of default is "
                    f"{risk.probability_of_default}."
                )

            if risk.foir is not None:
                parts.append(
                    f"FOIR is {risk.foir}%."
                )

        if policy_exceptions:

            parts.append(
                "Some policy parameters require "
                "configuration or review before a fully "
                "policy-driven decision can be made."
            )

        return " ".join(parts)

    # =========================================================
    # OFFICER SUMMARY
    # =========================================================

    def _build_officer_summary(
        self,
        strengths: list[str],
        concerns: list[str],
        policy_exceptions: list[str],
    ) -> str:

        parts: list[str] = []

        if strengths:
            parts.append(
                "Strengths: "
                + "; ".join(strengths)
            )

        if concerns:
            parts.append(
                "Concerns: "
                + "; ".join(concerns)
            )

        if policy_exceptions:
            parts.append(
                "Policy items requiring attention: "
                + "; ".join(policy_exceptions)
            )

        return " ".join(parts)

    # =========================================================
    # STRUCTURED EVIDENCE
    # =========================================================

    def _merge_items(
        self,
        deterministic: list[str],
        llm: list[str],
    ) -> list[str]:

        result: list[str] = []

        for item in deterministic + llm:

            if item and item not in result:
                result.append(item)

        return result

    def _build_llm_evidence(
        self,
        borrower: Borrower360,
        underwriting: UnderwritingResult,
        strengths: list[str],
        concerns: list[str],
        missing_information: list[str],
        policy_exceptions: list[str],
    ) -> GenAIEvidence:

        kyc_evidence = {}
        if borrower.kyc:
            kyc_evidence = {
                "pan_present" : bool(borrower.kyc.pan),
                "aadhaar_kyc_status": (borrower.kyc.aadhaar_kyc_status),
                "ekyc_result_available": bool(borrower.kyc.ekyc_result),
                "dob_present": bool(borrower.kyc.dob),
                "address_present": bool(borrower.kyc.address),
            }

        bureau_evidence = {}
        if borrower.credit_bureau:
            bureau = borrower.credit_bureau
            bureau_evidence = {
                "score": bureau.score,
                "dpd": bureau.dpd,
                "enquiries": bureau.enquiries,
                "active_loans": bureau.active_loans,
                "total_outstanding": bureau.total_outstanding,
                "write_offs": bureau.write_offs,
            }

        bank_evidence = {}
        if borrower.bank_cash_flow:
            bank = borrower.bank_cash_flow
            income_patterns = bank.income_pattern or {}

            bank_evidence = {
                "credits": bank.credits,
                "debits": bank.debits,
                "balance": bank.balance,
                "emi": bank.emi,
                "bounce": bank.bounce,
                "transaction_count": bank.transaction_count,
                "income_trend": income_patterns.get("income_trend"),  
            }

        employment_evidence = {}
        if borrower.employment_business:
            employment = borrower.employment_business
            employment_evidence = {
                "salary": employment.salary,
                "employer_information_available": bool(employment.employer),
                "gst_information_available": bool(employment.gst),
                "udyam_information_available": bool(employment.udyam),
                "business_vintage": employment.business_vintage,
            }

        history_evidence = {}
        if borrower.internal_history:
            history = borrower.internal_history
            history_evidence = {
                "past_loans_count": len(history.past_loans or []),
                "repayment_records_count": len(history.repayment or []),
                "dpd_records_count": len(history.dpd or []),
                "collections_records_count": len(history.collections or []),
            }

        device_evidence = {}
        if borrower.device_behaviour:
            device = borrower.device_behaviour
            device_evidence = {
                "device_information_available": bool(device.device),
                "velocity": device.velocity,
                "session_patterns_available": bool(device.session_patterns), 
            }

        document_evidence = {}
        if borrower.documents:
            documents = borrower.documents
            document_evidence = {
                "payslip_count": len(documents.payslips or []),
                "bank_statement_count": len(documents.bank_statements or []),
                "invoice_count": len(documents.invoices or []),
                "business_proof_count": len(documents.business_proofs or []),  
            }

        return GenAIEvidence(
            application_id = None,
            customer_id = None,  

            # Borrower 360

            kyc = kyc_evidence,
            credit_bureau= bureau_evidence,            
            bank_cash_flow = bank_evidence,
            employment_business=employment_evidence,
            internal_history=history_evidence,
            device_behaviour=device_evidence,
            documents=document_evidence,

            # Underwriting evidence

            bureau_history= (
                underwriting.bureau_history.model_dump()
                if underwriting.bureau_history
                else {}
            ),

            bank_income= (
                underwriting.bank_income.model_dump()
                if underwriting.bank_income
                else {}
            ),
            
            fraud= (
                underwriting.fraud.model_dump()
                if underwriting.fraud
                else {}
            ),

            policy= (
                underwriting.policy.model_dump()
                if underwriting.policy
                else {}
            ),

            risk_assessment=(
                underwriting.risk_assessment.model_dump()
                if underwriting.risk_assessment
                else {}
            ),

            decision=(
                underwriting.decision.model_dump()
                if underwriting.decision
                else {}
            ),

            completeness=(
                underwriting.completeness.model_dump()
                if underwriting.completeness
                else {}
            ),
        
            # Deterministic findings

            strengths=strengths,
            concerns=concerns,
            missing_information=missing_information,
            policy_exceptions=policy_exceptions,
        )      

    # =========================================================
    # LLM PROMPT
    # =========================================================

    def _build_llm_prompt(
        self,
        evidence: dict,
    ) -> str:

        evidence_json = json.dumps(
            evidence,
            indent=2,
            default=str,
        )

        return f"""
You are a credit analyst copilot assisting a human credit officer.

The deterministic underwriting engine is authoritative.
Never make, modify, or recommend a new approve/reject decision.

Use only the supplied evidence.
Never invent names, income, credit scores, assets, liabilities,
employment details, policy rules, or missing data.
Do not use example borrower data or placeholder values.

If evidence is unavailable, explicitly state that it is unavailable.
Do not interpret an empty object or empty list as evidence of a fact.

Return exactly one valid JSON object with this single field:

{{
  "llm_analyst_narrative": "string"
}}

The llm_analyst_narrative value must be a concise, evidence-based
explanation for a human credit analyst, with a maximum of 80 words.

Use only the supplied evidence. Do not invent borrower facts.
Mention relevant strengths, concerns, and uncertainties where supported.
If evidence is missing or conflicting, acknowledge the uncertainty.
Do not make or change an approve/reject decision.

Do not include markdown code fences or text outside the JSON object.
Do not output the literal word "string".

The evidence below contains the current deterministic analysis.
Preserve its meaning and do not contradict its findings.

Generate llm_analyst_narrative as a concise, evidence-based explanation
for a human credit analyst. Mention relevant strengths, concerns, and
uncertainties. Do not make or change an approve/reject decision.
Do not repeat the deterministic credit narrative verbatim.

The deterministic risk_segment and risk assessment findings are authoritative.
Do not independently infer or relabel the borrower's risk level.
If the evidence identifies HIGH_RISK, never describe the application as low
or medium risk, even when individual indicators are positive.
Describe positive indicators as strengths without overriding risk concerns.
Do not claim a low probability of default means the application is low risk
when the deterministic risk assessment classifies it as HIGH_RISK.
If evidence is missing or conflicting, explicitly acknowledge the uncertainty.

EVIDENCE:
{evidence_json}
""".strip()

    # =========================================================
    # LLM RESPONSE PARSER
    # =========================================================

    def _parse_llm_response(
        self,
        raw_response: str,
    ) -> GenAILLMResponse:

        if not raw_response:
            raise ValueError(
                "Empty GenAI response."
            )

        response_text = raw_response.strip()

        # -----------------------------------------------------
        # Remove markdown code fences if returned by the model
        # -----------------------------------------------------

        if response_text.startswith("```"):

            lines = response_text.splitlines()

            if lines and lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            response_text = "\n".join(lines).strip()

        # Parse JSON

        try:

            parsed = json.loads(
                response_text
            )

        except json.JSONDecodeError as exc:

            raise ValueError(
                "GenAI response is not valid JSON."
            ) from exc

        # Validate top-level object

        if not isinstance(parsed, dict):

            raise ValueError(
                "GenAI response must be a JSON object."
            )
        
        # Pydantic validation

        try:

            return GenAILLMResponse.model_validate(
                parsed
            )

        except Exception as exc:

            raise ValueError(
                "GenAI response failed schema validation."
            ) from exc

    
    def _validate_llm_narrative(
        self,
        narrative: str | None,
        underwriting: UnderwritingResult,
    ) -> str | None:
        if not narrative:
            return None

        risk = underwriting.risk_assessment
        if risk and risk.risk_segment == "HIGH_RISK":
            prohibited_phrases = (
                "low risk",
                "low-risk",
                "medium risk",
                "medium-risk",
            )

            normalized = narrative.lower()
            if any(phrase in normalized for phrase in prohibited_phrases):
                return None

        return narrative


genai_underwriting_service = GenAIUnderwritingService()