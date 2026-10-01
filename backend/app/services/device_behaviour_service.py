import uuid

from sqlalchemy.orm import Session

from backend.app.models.device_behaviour import DeviceBehaviour
from backend.app.schemas.device_behaviour import DeviceBehaviourCreate


class DeviceBehaviourService:

    def create_device_behaviour(
        self,
        db: Session,
        device_behaviour: DeviceBehaviourCreate,
    ):
        record = DeviceBehaviour(
            device_behaviour_id=f"DEV-{uuid.uuid4().hex[:12].upper()}",
            application_id=device_behaviour.application_id,
            device_id=device_behaviour.device_id,
            device_type=device_behaviour.device_type,
            operating_system=device_behaviour.operating_system,
            app_version=device_behaviour.app_version,
            ip_address=device_behaviour.ip_address,
            device_age_days=device_behaviour.device_age_days,
            login_count=device_behaviour.login_count,
            session_count=device_behaviour.session_count,
            failed_login_count=device_behaviour.failed_login_count,
            application_velocity=device_behaviour.application_velocity,
            device_velocity=device_behaviour.device_velocity,
            ip_velocity=device_behaviour.ip_velocity,
            behavioural_risk_score=device_behaviour.behavioural_risk_score,
            fraud_indicator=device_behaviour.fraud_indicator,
            analysis_reference=device_behaviour.analysis_reference,
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return record


device_behaviour_service = DeviceBehaviourService()