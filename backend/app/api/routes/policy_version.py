import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.policy_version_governance import (
    PolicyVersionAction,
    PolicyVersionCreate,
    PolicyVersionResponse,
    PolicyVersionRollback,
)
from backend.app.services.audit_log_service import audit_log_service
from backend.app.services.policy_version_service import (
    policy_version_service,
)


router = APIRouter(
    prefix="/policy-governance",
    tags=["Policy Governance"],
)


@router.post(
    "",
    response_model=PolicyVersionResponse,
)
def create_policy_version(
    request: PolicyVersionCreate,
    db: Session = Depends(get_db),
):
    try:
        result = policy_version_service.create_policy_version(
            db=db,
            policy_version=request.policy_version,
            effective_from=request.effective_from,
            effective_to=request.effective_to,
            policy_reference=request.policy_reference,
            governance_notes=request.governance_notes,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=None,
            actor_type="USER",
            actor_reference="POLICY_GOVERNANCE",
            action="POLICY_VERSION_CREATED",
            entity_type="POLICY_VERSION",
            entity_reference=result.policy_version,
            description=(
                f"Policy version {result.policy_version} created."
            ),
            previous_state=None,
            new_state=result.status,
            request_reference=result.policy_version,
            policy_version=result.policy_version,
        )

        db.commit()
        db.refresh(result)

        return result

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="POLICY_VERSION_CREATION_FAILED",
        )


@router.get(
    "",
    response_model=list[PolicyVersionResponse],
)
def list_policy_versions(
    db: Session = Depends(get_db),
):
    return policy_version_service.list_policy_versions(
        db=db,
    )


@router.get(
    "/{policy_version}",
    response_model=PolicyVersionResponse,
)
def get_policy_version(
    policy_version: str,
    db: Session = Depends(get_db),
):
    try:
        return policy_version_service.get_policy_version(
            db=db,
            policy_version=policy_version,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.post(
    "/activate",
    response_model=PolicyVersionResponse,
)
def activate_policy_version(
    request: PolicyVersionAction,
    db: Session = Depends(get_db),
):
    policy_version: request.policy_version
    
    try:
        policy = policy_version_service.get_policy_version(
            db=db,
            policy_version=policy_version,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    try:
        previous_state = policy.status

        result = policy_version_service.activate_policy(
            db=db,
            policy_version=policy_version,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=None,
            actor_type="USER",
            actor_reference=request.actor_id,
            action="POLICY_VERSION_ACTIVATED",
            entity_type="POLICY_VERSION",
            entity_reference=result.policy_version,
            description=(
                f"Policy version {result.policy_version} activated."
            ),
            previous_state=previous_state,
            new_state=result.status,
            request_reference=result.policy_version,
            policy_version=result.policy_version,
        )

        db.commit()
        db.refresh(result)

        return result

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="POLICY_VERSION_ACTIVATION_FAILED",
        )


@router.post(
    "/deactivate",
    response_model=PolicyVersionResponse,
)
def deactivate_policy_version(
    request: PolicyVersionAction,
    db: Session = Depends(get_db),
):

    policy_version: request.policy_version
    try:
        policy = policy_version_service.get_policy_version(
            db=db,
            policy_version=policy_version,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    try:
        previous_state = policy.status

        result = policy_version_service.deactivate_policy(
            db=db,
            policy_version=policy_version,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=None,
            actor_type="USER",
            actor_reference=request.actor_id,
            action="POLICY_VERSION_DEACTIVATED",
            entity_type="POLICY_VERSION",
            entity_reference=result.policy_version,
            description=(
                f"Policy version {result.policy_version} deactivated."
            ),
            previous_state=previous_state,
            new_state=result.status,
            request_reference=result.policy_version,
            policy_version=result.policy_version,
        )

        db.commit()
        db.refresh(result)

        return result

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="POLICY_VERSION_DEACTIVATION_FAILED",
        )


@router.post(
    "/retire",
    response_model=PolicyVersionResponse,
)
def retire_policy_version(
    request: PolicyVersionAction,
    db: Session = Depends(get_db),
):

    policy_version: request.policy_version

    try:
        policy = policy_version_service.get_policy_version(
            db=db,
            policy_version=policy_version,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    try:
        previous_state = policy.status

        result = policy_version_service.retire_policy(
            db=db,
            policy_version=policy_version,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=None,
            actor_type="USER",
            actor_reference=request.actor_id,
            action="POLICY_VERSION_RETIRED",
            entity_type="POLICY_VERSION",
            entity_reference=result.policy_version,
            description=(
                f"Policy version {result.policy_version} retired."
            ),
            previous_state=previous_state,
            new_state=result.status,
            request_reference=result.policy_version,
            policy_version=result.policy_version,
        )

        db.commit()
        db.refresh(result)

        return result

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="POLICY_VERSION_RETIREMENT_FAILED",
        )


@router.post(
    "/rollback",
    response_model=PolicyVersionResponse,
)
def rollback_policy_version(
    request: PolicyVersionRollback,
    db: Session = Depends(get_db),
):
    try:
        result = policy_version_service.rollback_policy(
            db=db,
            target_policy_version=request.target_policy_version,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=None,
            actor_type="USER",
            actor_reference=request.actor_id,
            action="POLICY_VERSION_ROLLBACK",
            entity_type="POLICY_VERSION",
            entity_reference=result.policy_version,
            description=(
                f"Policy rollback completed. "
                f"Active policy version: {result.policy_version}."
            ),
            previous_state="ACTIVE",
            new_state=result.status,
            request_reference=result.policy_version,
            policy_version=result.policy_version,
        )

        db.commit()
        db.refresh(result)

        return result

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="POLICY_VERSION_ROLLBACK_FAILED",
        )