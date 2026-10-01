from pydantic import BaseModel


class RiskSegmentationResult(BaseModel):
    risk_segment: str | None = None