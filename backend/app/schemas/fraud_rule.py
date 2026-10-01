from typing import Literal
from pydantic import BaseModel

FraudRuleStatus = Literal[
    "PASS",
    "FAIL",
    "EXCEPTION",
    "NOT_EVALUATED",
]

class FraudRuleResult(BaseModel):
    rule_id: str 
    status: FraudRuleStatus
    reason: str