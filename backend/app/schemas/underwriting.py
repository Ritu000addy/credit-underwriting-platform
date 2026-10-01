from pydantic import BaseModel

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