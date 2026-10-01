from pydantic import BaseModel, Field


class ReasonCodeResult(BaseModel):
    reason_codes: list[str] = Field(default_factory=list)