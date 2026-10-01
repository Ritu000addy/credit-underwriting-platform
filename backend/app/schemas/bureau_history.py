from pydantic import BaseModel, Field

class BureauCheck(BaseModel):
    check_id: str
    status: str
    reason: str

class InternalHistoryCheck(BaseModel):
    check_id: str
    status: str
    reason: str

class BureauHistoryResult(BaseModel):
    status: str
    bureau_checks: list[BureauCheck]
    internal_history_checks: list[InternalHistoryCheck]
    reason_codes: list[str] = Field(default_factory=list)