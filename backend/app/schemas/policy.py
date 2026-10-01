from typing import Literal

from pydantic import BaseModel

PolicyRuleStatus = Literal["PASS", "FAIL", "EXCEPTION", "NOT_EVALUATED"]

class PolicyRuleResult(BaseModel):
    rule_id: str
    status: PolicyRuleStatus
    reason: str

class PolicyEvaluationResult(BaseModel):
    policy_status: Literal["APPROVE", "REFER", "REJECT"]
    rules: list[PolicyRuleResult]