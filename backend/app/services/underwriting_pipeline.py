from backend.app.schemas.application import ApplicationCreate
from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.underwriting import UnderwritingResult

from backend.app.services.completeness_checker import completeness_checker
from backend.app.services.kyc_validator import kyc_validator
from backend.app.services.bureau_history_validator import bureau_history_validator
from backend.app.services.bank_income_validator import bank_income_validator
from backend.app.services.fraud_validator import fraud_validator
from backend.app.services.policy_engine import policy_engine
from backend.app.services.risk_assessment_service import risk_assessment_service
from backend.app.services.decision_orchestrator import decision_orchestrator

class UnderwritingPipeline:

    def process(
        self,
        application: ApplicationCreate,
        borrower: Borrower360,
        policy_config: dict,
        policy_metadata: dict,
    ) -> UnderwritingResult:

        result = UnderwritingResult(
            application_id= application.application_id,
            customer_id=application.customer_id,
        )

        # Stage 1: Completeness

        result.completeness = completeness_checker.check(
            application,
            borrower,
        )

        if result.completeness.status != "COMPLETE":
            return result
        
        # Stage 2: KYC

        result.kyc = kyc_validator.validate(borrower)

        if result.kyc.status != "PASS":
            return result
        
        # Stage 3: Bureau + History

        result.bureau_history = bureau_history_validator.validate(
            borrower
        )

        if result.bureau_history.status != "PASS":
            return result
        
        # Stage 4: Bank + Income

        result.bank_income = bank_income_validator.validate(
            borrower
        )

        if result.bank_income.status != "PASS":
            return result
        
        # Stage 5: Fraud Screening

        result.fraud = fraud_validator.validate(
            borrower
        )

        if result.fraud.status != "PASS":
            return result

        # Stage 6: Risk Assessement
        result.risk_assessment = risk_assessment_service.assess(
            application,
            borrower,
            annual_interest_rate=application.annual_interest_rate,
        )
        
        # Stage 7: Policy Evaluation

        result.policy = policy_engine.evaluate(
            application=application,
            borrower=borrower,
            foir=result.risk_assessment.foir,
            policy_config=policy_config,
            policy_metadata=policy_metadata,
        )

        result.decision = decision_orchestrator.decide(
            application_id=application.application_id,
            policy_result=result.policy,
            risk_result=result.risk_assessment,
        )

        return result
        
underwriting_pipeline = UnderwritingPipeline()