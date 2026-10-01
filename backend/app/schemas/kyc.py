from pydantic import BaseModel, Field

class KYCCheck(BaseModel):
    check_id: str
    status: str
    reason: str

class KYCCheckResult(BaseModel):
    status: str
    checks: list[KYCCheck]
    reason_codes: list[str] = Field(default_factory=list)