from decimal import Decimal

from backend.app.schemas.credit_decision import CreditDecisionOutput
from backend.app.schemas.policy import PolicyEvaluationResult
from backend.app.schemas.risk_assessment import RiskAssessmentResult
from backend.app.services.reason_code_service import (
    reason_code_service,
)

class DecisionOrchestrator:

    def decide(
        self,
        application_id: str,
        policy_result: PolicyEvaluationResult,
        risk_result: RiskAssessmentResult,
    ) -> CreditDecisionOutput:

        policy_not_evaluated_count = sum(
            1
            for rule in policy_result.rules
            if rule.status == "NOT_EVALUATED"
        )

        reason_code_result = reason_code_service.generate(
            credit_score=risk_result.credit_score,
            probability_of_default=risk_result.probability_of_default,
            affordability_score=risk_result.affordability_score,
            repayment_propensity=risk_result.repayment_propensity,
            fraud_risk_level=risk_result.fraud_risk_level,
            income_stability_score=risk_result.income_stability_score,
            foir=risk_result.foir,
            policy_status=policy_result.policy_status,
            policy_not_evaluated_count=policy_not_evaluated_count,
        )

        fraud_reason_codes = risk_result.fraud_reason_codes or []

        fraud_assessment_incomplete = (
            risk_result.fraud_score is None
            or risk_result.fraud_risk_level is None
            or risk_result.fraud_confidence is None
            or risk_result.fraud_confidence < Decimal("1")
            or any(
                code.startswith("FRAUD_DATA_")
                for code in fraud_reason_codes
            )
        )

        fraud_findings_present = (
            risk_result.fraud_score is not None
            and risk_result.fraud_score > Decimal("0")
        )

        final_decision = policy_result.policy_status

        if (
            final_decision == "APPROVE"
            and (
                fraud_assessment_incomplete
                or fraud_findings_present
            )
        ):
            final_decision = "REFER"

        decision_reason_codes = list(
            reason_code_result.reason_codes
        )

        if (
            fraud_assessment_incomplete
            and "FRAUD_ASSESSMENT_INCOMPLETE"
            not in decision_reason_codes
        ):
            decision_reason_codes.append(
                "FRAUD_ASSESSMENT_INCOMPLETE"
            )

        if (
            fraud_findings_present
            and "FRAUD_RISK_REVIEW_REQUIRED"
            not in decision_reason_codes
        ):
            decision_reason_codes.append(
                "FRAUD_RISK_REVIEW_REQUIRED"
            )

        return CreditDecisionOutput(
            application_id = application_id,

            # Risk outputs
            credit_score=risk_result.credit_score,
            risk_grade=risk_result.risk_grade,
            probability_of_default= risk_result.probability_of_default,

            affordability_score=risk_result.affordability_score,
            repayment_propensity=risk_result.repayment_propensity,
            fraud_score=risk_result.fraud_score,
            fraud_risk_level=risk_result.fraud_risk_level,
            fraud_confidence=risk_result.fraud_confidence,
            fraud_reason_codes=risk_result.fraud_reason_codes,

            income_stability_score=risk_result.income_stability_score,
            income_trend=risk_result.income_trend,
            risk_segment=risk_result.risk_segment,

            # Loan Recommendation
            recommended_amount=risk_result.recommended_amount,
            recommended_tenure=risk_result.recommended_tenure,
            recommended_emi=risk_result.recommended_emi,

            # Affordability
            foir=risk_result.foir,

            # Temporary Safe Decision
            decision=final_decision,
            confidence=risk_result.confidence,
            
            # Preserve Model Reason Codes
            reason_codes=decision_reason_codes,

            # Preserve Policy Evaluation
            policy_checks=policy_result.rules,

            model_version=risk_result.model_version,
            model_features=risk_result.model_features,
            policy_version=policy_result.policy_version,
            effective_from=policy_result.effective_from,
            effective_to=policy_result.effective_to,
        )

decision_orchestrator = DecisionOrchestrator()