import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.underwriting_feature_snapshot import (
    UnderwritingFeatureSnapshot,
)


class UnderwritingFeatureSnapshotService:

    def create_snapshot(
        self,
        db: Session,
        application_id: str,
        decision_id: str,
        model_version: str | None,
        features: dict[str, Any],
        feature_version: str = "1.0",
    ) -> UnderwritingFeatureSnapshot:

        snapshot = UnderwritingFeatureSnapshot(
            feature_snapshot_id=(
                f"FEAT-{uuid.uuid4().hex[:12].upper()}"
            ),
            application_id=application_id,
            decision_id=decision_id,
            model_version=model_version,
            feature_version=feature_version,
            features=features,
        )

        db.add(snapshot)
        db.flush()
        db.refresh(snapshot)

        return snapshot


underwriting_feature_snapshot_service = (
    UnderwritingFeatureSnapshotService()
)