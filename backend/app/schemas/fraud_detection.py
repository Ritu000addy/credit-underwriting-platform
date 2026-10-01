from pydantic import BaseModel, Field

class FraudDetectionCheck(BaseModel):
    check_id: str
    status: str 
    reason: str 

class FraudDetectionResult(BaseModel):
    status: str 
    checks: list[FraudDetectionCheck] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)