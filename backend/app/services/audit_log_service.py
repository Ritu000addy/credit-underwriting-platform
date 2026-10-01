from sqlalchemy.orm import Session

from backend.app.models.audit_log import AuditLog


class AuditLogService:

    def log(
        self,
        db: Session,
        audit_log_id: str,
        actor_type: str,
        action: str,
        application_id: str | None = None,
        actor_reference: str | None = None,
        entity_type: str | None = None,
        entity_reference: str | None = None,
        description: str | None = None,
        model_version: str | None = None,
        policy_version: str | None = None,
    ) -> AuditLog:

        audit_log = AuditLog(
            audit_log_id=audit_log_id,
            application_id=application_id,
            actor_type=actor_type,
            actor_reference=actor_reference,
            action=action,
            entity_type=entity_type,
            entity_reference=entity_reference,
            description=description,
            model_version=model_version,
            policy_version=policy_version,
        )

        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        return audit_log

    def get_by_application(
        self,
        db: Session,
        application_id: str,
    ) -> list[AuditLog]:

        return (
            db.query(AuditLog)
            .filter(
                AuditLog.application_id == application_id
            )
            .order_by(AuditLog.created_at.asc())
            .all()
        )

audit_log_service = AuditLogService()