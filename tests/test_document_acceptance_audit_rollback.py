
import json
import uuid

from fastapi.testclient import TestClient

from types import SimpleNamespace

from backend.app.core.security import get_current_user

import backend.app.api.routes.documents as documents_route
from backend.app.database import SessionLocal
from backend.app.main import app
from backend.app.models.audit_log import AuditLog
from backend.app.models.bank_analysis import BankAnalysis
from backend.app.models.customer import Customer
from backend.app.models.document import Document
from backend.app.models.loan_application import LoanApplication


def seed_document_case():
    suffix = uuid.uuid4().hex[:12].upper()
    application_id = f"DOC-ROLLBACK-APP-{suffix}"
    customer_id = f"DOC-ROLLBACK-CUST-{suffix}"
    document_id = f"DOC-ROLLBACK-{suffix}"
    analysis_reference = f"DOC-INTEL-ROLLBACK-{suffix}"

    extraction = {
        "status": "EXTRACTION_COMPLETE",
        "document_id": document_id,
        "application_id": application_id,
        "document_type": "BANK_STATEMENT",
        "analysis_reference": analysis_reference,
        "fields": {
            "monthly_credits": {
                "value": "80000",
                "confidence": 0.98,
                "evidence": "Monthly credits total: INR 80,000",
            },
        },
        "missing_fields": [],
        "conflicts": [],
        "warnings": [],
        "provider": "TEST",
        "model_name": "TEST",
    }

    db = SessionLocal()
    try:
        db.add(
            Customer(
                customer_id=customer_id,
                kyc_status="VERIFIED",
            )
        )
        db.flush()

        db.add(
            LoanApplication(
                application_id=application_id,
                customer_id=customer_id,
                product="SYNTHETIC_TEST",
                requested_amount=150000,
                loan_tenure_months=12,
                annual_interest_rate=12,
                status="SUBMITTED",
            )
        )
        db.flush()

        db.add(
            Document(
                document_id=document_id,
                application_id=application_id,
                document_type="BANK_STATEMENT",
                document_name="synthetic-test-statement",
                extracted_data=json.dumps(extraction),
                analysis_reference=analysis_reference,
            )
        )

        db.commit()

        return {
            "application_id": application_id,
            "customer_id": customer_id,
            "document_id": document_id,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def cleanup_document_case(case):
    db = SessionLocal()
    try:
        application_id = case["application_id"]

        db.query(AuditLog).filter(
            AuditLog.application_id == application_id
        ).delete(synchronize_session=False)

        db.query(BankAnalysis).filter(
            BankAnalysis.application_id == application_id
        ).delete(synchronize_session=False)

        db.query(Document).filter(
            Document.application_id == application_id
        ).delete(synchronize_session=False)

        db.query(LoanApplication).filter(
            LoanApplication.application_id == application_id
        ).delete(synchronize_session=False)

        db.query(Customer).filter(
            Customer.customer_id == case["customer_id"]
        ).delete(synchronize_session=False)

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def test_document_acceptance_rolls_back_when_audit_fails(monkeypatch):
    case = seed_document_case()

    def fail_audit(**kwargs):
        raise RuntimeError("SIMULATED_ACCEPTANCE_AUDIT_FAILURE")

    monkeypatch.setattr(
        documents_route.audit_log_service,
        "log",
        fail_audit,
    )

    try:
        client = TestClient(app, raise_server_exceptions=False)

        monkeypatch.setitem(
            app.dependency_overrides,
            get_current_user,
            lambda: SimpleNamespace(
                user_id="AUTH-REVIEWER-ROLLBACK",
                username="reviewer.rollback",
                role="OPERATIONS",
                is_active=True,
            ),
        )

        response = client.post(
            f"/documents/{case['document_id']}/accept-bank-analysis",
            json={
                "reviewer_id": "reviewer.rollback",
                "confirmed": True,
                "accepted_fields": ["monthly_credits"],
                "acknowledged_conflicts": [],
            },
        )

        assert response.status_code == 500, response.text

        db = SessionLocal()
        try:
            # The source document must remain available.
            document = db.get(Document, case["document_id"])
            assert document is not None

            # The bank-analysis insert must have been rolled back.
            analyses = (
                db.query(BankAnalysis)
                .filter(
                    BankAnalysis.application_id
                    == case["application_id"]
                )
                .all()
            )
            assert analyses == []

            # The audit failed, so no acceptance audit entry
            # should have been committed either.
            audit_rows = (
                db.query(AuditLog)
                .filter(
                    AuditLog.application_id
                    == case["application_id"],
                    AuditLog.action
                    == "DOCUMENT_BANK_ANALYSIS_ACCEPTED",
                )
                .all()
            )
            assert audit_rows == []

        finally:
            db.close()

    finally:
        cleanup_document_case(case)
