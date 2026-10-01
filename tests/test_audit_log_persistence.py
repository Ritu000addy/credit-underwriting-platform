from backend.app.database import SessionLocal
from backend.app.services.audit_log_service import audit_log_service


db = SessionLocal()

try:
    result = audit_log_service.log(
        db=db,
        audit_log_id="DEV-AUDIT-001",
        application_id="PERSIST-TEST-001",
        actor_type="SYSTEM",
        actor_reference="DEV_TEST",
        action="CREDIT_DECISION_TEST",
        entity_type="CREDIT_DECISION",
        entity_reference="DEC-PERSIST-TEST-001",
        description="Development audit-log persistence test.",
        model_version="DEV-SYNTHETIC-LOGREG-01",
        policy_version="POL-DEV-TEST-01",
    )

    print("AUDIT LOG SAVED")
    print("audit_log_id:", result.audit_log_id)
    print("application_id:", result.application_id)
    print("actor_type:", result.actor_type)
    print("actor_reference:", result.actor_reference)
    print("action:", result.action)
    print("entity_type:", result.entity_type)
    print("entity_reference:", result.entity_reference)
    print("description:", result.description)
    print("model_version:", result.model_version)
    print("policy_version:", result.policy_version)

finally:
    db.close()