from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

from backend.app.schemas.completeness import CompletenessResult
from backend.app.schemas.kyc import KYCCheckResult
from backend.app.schemas.bureau_history import BureauHistoryResult
from backend.app.schemas.bank_income import BankIncomeResult
from backend.app.schemas.fraud import FraudScreeningResult
from backend.app.schemas.policy import PolicyEvaluationResult
from backend.app.schemas.risk_assessment import RiskAssessmentResult
from backend.app.schemas.credit_decision import CreditDecisionOutput

class UnderwritingResult(BaseModel):
    application_id: str
    customer_id: str

    completeness: CompletenessResult | None = None
    kyc: KYCCheckResult | None = None
    bureau_history: BureauHistoryResult | None = None
    bank_income: BankIncomeResult | None = None
    fraud: FraudScreeningResult | None = None
    policy: PolicyEvaluationResult | None = None
    risk_assessment: RiskAssessmentResult | None = None
    decision: CreditDecisionOutput | None = None


class UnderwritingDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    decision_id: str
    application_id: str
    credit_score: int | None = None
    risk_grade: str | None = None
    probability_of_default: Decimal | None = None
    affordability_score: Decimal | None = None
    repayment_propensity: Decimal | None = None
    fraud_score: Decimal | None = None
    income_stability_score: Decimal | None = None
    risk_segment: str | None = None
    recommended_amount: Decimal | None = None
    recommended_tenure: int | None = None
    recommended_emi: Decimal | None = None
    foir: Decimal | None = None
    decision: str
    confidence: Decimal | None = None
    reason_codes: list[str] = []
    model_version: str | None = None
    policy_version: str | None = None
    created_at: datetime