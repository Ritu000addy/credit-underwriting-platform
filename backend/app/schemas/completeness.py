from pydantic import BaseModel, Field

class CompletenessResult(BaseModel):
    status: str
    missing_fields: list[str] = Field(default_factory=list)