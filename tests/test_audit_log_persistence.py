import uuid

from backend.app.database import SessionLocal
from backend.app.models.audit_log import AuditLog
from backend.app.services.audit_log_service import audit_log_service

def test_audit_log_persists_after_commit():
    audit_log_id = f"TEST-AUDIT-{uuid.uuid4().hex[:12].upper()}"

    try:
        # Create and commit the audit record.
        db = SessionLocal()

        try:
            result = audit_log_service.log(
                db=db,
                audit_log_id=audit_log_id,
                application_id=None,
                actor_type="SYSTEM",
                actor_reference="PYTEST",
                action="AUDIT_PERSISTENCE_TEST",
                entity_type="TEST",
                entity_reference=audit_log_id,
                description="Sythetic pytest audit persistence test.",
                model_version="TEST-MODEL",
                policy_version="TEST-POLICY",
            )

            assert result.audit_log_id == audit_log_id
            db.commit()

        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        # Verify persistence using an independent session.
        verify_db = SessionLocal()
        try:
            persisted = verify_db.get(AuditLog, audit_log_id)

            assert persisted is not None
            assert persisted.action == "AUDIT_PERSISTENCE_TEST"
            assert persisted.actor_reference == "PYTEST"
            assert persisted.entity_reference == audit_log_id
        finally:
            verify_db.close()

    finally:
        # Remove only this test's uniquely identified record.
        cleanup_db = SessionLocal()
        try:
            cleanup_db.query(AuditLog).filter(
                AuditLog.audit_log_id == audit_log_id
            ).delete(synchronize_session=False)
            cleanup_db.commit()
        except Exception:
            cleanup_db.rollback()
            raise
        finally:
            cleanup_db.close()