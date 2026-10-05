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
            decision=policy_result.policy_status,
            confidence=risk_result.confidence,
            
            # Preserve Model Reason Codes
            reason_codes=reason_code_result.reason_codes,

            # Preserve Policy Evaluation
            policy_checks=policy_result.rules,

            model_version=risk_result.model_version,
            model_features=risk_result.model_features,
            policy_version=policy_result.policy_version,
            effective_from=policy_result.effective_from,
            effective_to=policy_result.effective_to,
        )

decision_orchestrator = DecisionOrchestrator()