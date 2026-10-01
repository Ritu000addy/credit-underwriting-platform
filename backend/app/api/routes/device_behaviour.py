from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.device_behaviour import DeviceBehaviourCreate
from backend.app.services.device_behaviour_service import device_behaviour_service


router = APIRouter(
    prefix="/device-behaviour",
    tags=["Source Data Ingestion"],
)


@router.post("")
def create_device_behaviour(
    device_behaviour: DeviceBehaviourCreate,
    db: Session = Depends(get_db),
):
    result = device_behaviour_service.create_device_behaviour(
        db=db,
        device_behaviour=device_behaviour,
    )

    return {
        "message": "Device / behaviour data created successfully",
        "device_behaviour": {
            "device_behaviour_id": result.device_behaviour_id,
            "application_id": result.application_id,
            "device_id": result.device_id,
            "device_type": result.device_type,
            "operating_system": result.operating_system,
            "app_version": result.app_version,
            "ip_address": result.ip_address,
            "device_age_days": result.device_age_days,
            "login_count": result.login_count,
            "session_count": result.session_count,
            "failed_login_count": result.failed_login_count,
            "application_velocity": result.application_velocity,
            "device_velocity": result.device_velocity,
            "ip_velocity": result.ip_velocity,
            "behavioural_risk_score": result.behavioural_risk_score,
            "fraud_indicator": result.fraud_indicator,
            "analysis_reference": result.analysis_reference,
            "analyzed_at": result.analyzed_at,
        },
    }