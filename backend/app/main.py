from fastapi import FastAPI

from backend.app.database import engine
from backend.app.models.base import Base
import backend.app.models

from backend.app.api.routes.customers import router as customers_router
from backend.app.api.routes.applications import router as application_router 
from backend.app.api.routes.underwriting import router as underwriting_router
from backend.app.api.routes.sanctions import router as sanctions_router
from backend.app.api.routes.agreements import router as agreements_router
from backend.app.api.routes.mandates import router as mandates_router
from backend.app.api.routes.disbursements import router as disbursements_router
from backend.app.api.routes.post_disbursement import router as post_disbursement_router
from backend.app.api.routes.repayments import router as repayments_router
from backend.app.api.routes.collections import router as collections_router
from backend.app.api.routes.audit import router as audit_router
from backend.app.api.routes.lms import router as lms_router
from backend.app.api.routes.bureau import router as bureau_router
from backend.app.api.routes.bank_analysis import router as bank_analysis_router
from backend.app.api.routes.employment import router as employment_router
from backend.app.api.routes.internal_history import router as internal_history_router
from backend.app.api.routes.device_behaviour import router as device_behaviour_router
from backend.app.api.routes.documents import router as documents_router
from backend.app.api.routes.borrower360 import router as borrower360_router
from backend.app.api.routes.underwriting_validation import (
    router as underwriting_validation_router,
)
from backend.app.api.routes.policy_validation import (
    router as policy_validation_router,
)
from backend.app.api.routes.aadhaar_kyc import router as aadhaar_kyc_router
from backend.app.api.routes.genai_underwriting import router as genai_underwriting_router
from backend.app.api.routes.manual_review import router as manual_review_router


app = FastAPI(
    title="AI Credit Underwriting Platform",
    description="GenAI-enabled credit underwriting and disbursement platform",
    version="0.1.0"
)

Base.metadata.create_all(bind=engine)

app.include_router(customers_router)
app.include_router(application_router)
app.include_router(underwriting_router)
app.include_router(sanctions_router)
app.include_router(agreements_router)
app.include_router(mandates_router)
app.include_router(disbursements_router)
app.include_router(post_disbursement_router)
app.include_router(repayments_router)
app.include_router(collections_router)
app.include_router(audit_router)
app.include_router(lms_router)
app.include_router(bureau_router)
app.include_router(bank_analysis_router)
app.include_router(employment_router)
app.include_router(internal_history_router)
app.include_router(device_behaviour_router)
app.include_router(documents_router)
app.include_router(borrower360_router)
app.include_router(underwriting_validation_router)
app.include_router(policy_validation_router)
app.include_router(aadhaar_kyc_router)
app.include_router(genai_underwriting_router)
app.include_router(manual_review_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Credit Underwriting Platform",
        "version": "0.1.0",
    }