from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.core.responses import success_response
from backend.app.database import get_db
from backend.app.schemas.common import ApiResponse
from backend.app.services.audit_log_service import audit_log_service


router = APIRouter(
    prefix="/audit",
    tags=["Audit"],
)


@router.get(
    "/{application_id}",
    response_model=ApiResponse[dict[str, Any]],
)
def get_application_audit(
    application_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    results = audit_log_service.get_by_application(
        db=db,
        application_id=application_id,
    )

    response_data = {
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
                "previous_state": result.previous_state,
                "new_state": result.new_state,
                "request_reference": result.request_reference,
                "model_version": result.model_version,
                "policy_version": result.policy_version,
                "created_at": result.created_at,
            }
            for result in results
        ],
    }

    return success_response(
        request=request,
        data=response_data,
        message="Application audit logs retrieved successfully.",
    )