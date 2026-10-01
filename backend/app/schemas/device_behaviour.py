from pydantic import BaseModel
from typing import Optional


class DeviceBehaviourCreate(BaseModel):
    application_id: str

    device_id: Optional[str] = None
    device_type: Optional[str] = None
    operating_system: Optional[str] = None
    app_version: Optional[str] = None

    ip_address: Optional[str] = None
    device_age_days: Optional[int] = None

    login_count: Optional[int] = None
    session_count: Optional[int] = None
    failed_login_count: Optional[int] = None

    application_velocity: Optional[int] = None
    device_velocity: Optional[int] = None
    ip_velocity: Optional[int] = None

    behavioural_risk_score: Optional[float] = None
    fraud_indicator: Optional[str] = None

    analysis_reference: Optional[str] = None