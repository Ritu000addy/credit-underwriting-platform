from pydantic import BaseModel

class FraudFeatures(BaseModel):

    # Identity
    identity_data_available: int | None = None
    identity_mismatch_flag: int | None = None

    # Device
    device_data_available: int | None = None
    multiple_device_flag: int | None = None
    device_velocity: int | None = None

    # Transaction
    transaction_data_available: int | None = None
    transaction_velocity: int | None = None
    transaction_anomaly_flag: int | None = None

    # Document
    document_data_available: int | None = None
    document_anomaly_flag: int | None = None

    # Behavior
    behavioural_data_available: int | None = None
    session_anomaly_flag: int | None = None