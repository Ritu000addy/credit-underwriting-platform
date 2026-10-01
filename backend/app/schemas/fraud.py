from pydantic import BaseModel, Field

class FraudCheck(BaseModel):
    check_id: str
    status: str
    reason: str

class FraudScreeningResult(BaseModel):
    status: str
    checks: list[FraudCheck]
    reason_codes: list[str] = Field(default_factory=list)