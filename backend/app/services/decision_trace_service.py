import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.decision_trace import DecisionTrace


class DecisionTraceService:

    def create_trace(
        self,
        db: Session,
        application_id: str,
        decision_id: str,
        feature_snapshot_id: str | None,
        decision: str,
        model_version: str | None,
        policy_version: str,
        effective_from: str | None,
        effective_to: str | None,
        model_outputs: dict[str, Any] | None,
        policy_evaluation: list[dict[str, Any]] | None,
        reason_codes: list[str] | None,
        decision_metadata: dict[str, Any] | None = None,
    ) -> DecisionTrace:

        trace = DecisionTrace(
            trace_id=f"TRACE-{uuid.uuid4().hex[:12].upper()}",
            application_id=application_id,
            decision_id=decision_id,
            feature_snapshot_id=feature_snapshot_id,
            decision=decision,
            model_version=model_version,
            policy_version=policy_version,
            effective_from=effective_from,
            effective_to=effective_to,
            model_outputs=model_outputs,
            policy_evaluation=policy_evaluation,
            reason_codes=reason_codes,
            decision_metadata=decision_metadata,
        )

        db.add(trace)
        db.commit()
        db.refresh(trace)

        return trace

    def get_by_decision(
        self,
        db: Session,
        decision_id: str,
    ) -> DecisionTrace | None:

        return (
            db.query(DecisionTrace)
            .filter(
                DecisionTrace.decision_id == decision_id
            )
            .first()
        )

    def get_by_application(
        self,
        db: Session,
        application_id: str,
    ) -> list[DecisionTrace]:

        return (
            db.query(DecisionTrace)
            .filter(
                DecisionTrace.application_id == application_id
            )
            .order_by(DecisionTrace.created_at.asc())
            .all()
        )


decision_trace_service = DecisionTraceService()