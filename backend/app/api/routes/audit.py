from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services.audit_log_service import audit_log_service


router = APIRouter(
    prefix="/audit",
    tags=["Audit"],
)


@router.get("/{application_id}")
def get_application_audit(
    application_id: str,
    db: Session = Depends(get_db),
):
    results = audit_log_service.get_by_application(
        db=db,
        application_id=application_id,
    )

    return {
        "application_id": application_id,
        "audit_logs": [
            {
                "audit_log_id": result.audit_log_id,
                "actor_type": result.actor_type,
                "actor_reference": result.actor_reference,
                "action": result.action,
                "entity_type": result.entity_type,
                "entity_reference": result.entity_reference,
                "description": result.description,
                "model_version": result.model_version,
                "policy_version": result.policy_version,
                "created_at": result.created_at,
            }
            for result in results
        ],
    }