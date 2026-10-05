from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class UnderwritingFeatureSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    feature_snapshot_id: str
    application_id: str
    decision_id: str
    model_version: str | None = None
    feature_version: str
    features: dict[str, Any]
    created_at: datetime