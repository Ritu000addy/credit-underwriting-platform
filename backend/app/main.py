from fastapi import FastAPI

from backend.app.database import engine
from backend.app.models.base import Base
import backend.app.models

# ============================================================
# 1. LOS ORIGINATION
# ============================================================

from backend.app.api.routes.customers import router as customers_router
from backend.app.api.routes.applications import router as application_router

# ============================================================
# 2. SOURCE DATA INGESTION
# ============================================================

from backend.app.api.routes.aadhaar_kyc import router as aadhaar_kyc_router
from backend.app.api.routes.bureau import router as bureau_router
from backend.app.api.routes.bank_analysis import router as bank_analysis_router
from backend.app.api.routes.employment import router as employment_router
from backend.app.api.routes.device_behaviour import router as device_behaviour_router
from backend.app.api.routes.documents import router as documents_router
from backend.app.api.routes.internal_history import router as internal_history_router

# ============================================================
# 3. BORROWER 360
# ============================================================

from backend.app.api.routes.borrower360 import router as borrower360_router


# ============================================================
# 4. AI CREDIT UNDERWRITING
# ============================================================

from backend.app.api.routes.underwriting import router as underwriting_router
from backend.app.api.routes.underwriting_validation import (
    router as underwriting_validation_router,
)
from backend.app.api.routes.policy_validation import (
    router as policy_validation_router,
)


# ============================================================
# 5. GENAI UNDERWRITING
# ============================================================

from backend.app.api.routes.genai_underwriting import (
    router as genai_underwriting_router,
)


# ============================================================
# 6. MANUAL REVIEW
# ============================================================

from backend.app.api.routes.manual_review import router as manual_review_router

from backend.app.api.routes.review_exception import (
    router as review_exception_router,
)


# ============================================================
# 7. SANCTION
# ============================================================

from backend.app.api.routes.sanctions import router as sanctions_router


# ============================================================
# 8. AGREEMENT
# ============================================================

from backend.app.api.routes.agreements import router as agreements_router


# ============================================================
# 9. MANDATE
# ============================================================

from backend.app.api.routes.mandates import router as mandates_router


# ============================================================
# 10. DISBURSEMENT
# ============================================================

from backend.app.api.routes.disbursements import (
    router as disbursements_router,
)

# ============================================================
# 11. AUDIT
# ============================================================

from backend.app.api.routes.audit import router as audit_router

# ============================================================
# 12. RECONCILIATION
# ============================================================

from backend.app.api.routes.post_disbursement import (
    router as post_disbursement_router,
)

# ============================================================
# 13. REPAYMENT
# ============================================================

from backend.app.api.routes.repayments import router as repayments_router

# ============================================================
# 14. COLLECTIONS
# ============================================================

from backend.app.api.routes.collections import router as collections_router

# ============================================================
# 15. LMS
# ============================================================

from backend.app.api.routes.lms import router as lms_router



app = FastAPI(
    title="AI Credit Underwriting Platform",
    description="GenAI-enabled credit underwriting and disbursement platform",
    version="0.1.0"
)

Base.metadata.create_all(bind=engine)

# 1. LOS Origination
app.include_router(customers_router)
app.include_router(application_router)

# 2. Source Data Ingestion
app.include_router(aadhaar_kyc_router)
app.include_router(bureau_router)
app.include_router(bank_analysis_router)
app.include_router(employment_router)
app.include_router(device_behaviour_router)
app.include_router(documents_router)
app.include_router(internal_history_router)

# 3. Borrower 360
app.include_router(borrower360_router)

# 4. AI Credit Underwriting
app.include_router(underwriting_router)
app.include_router(underwriting_validation_router)
app.include_router(policy_validation_router)

# 5. GenAI Underwriting
app.include_router(genai_underwriting_router)

# 6. Manual Review
app.include_router(manual_review_router)
app.include_router(review_exception_router)

# 7. Sanction
app.include_router(sanctions_router)

# 8. Agreement
app.include_router(agreements_router)

# 9. Mandate
app.include_router(mandates_router)

# 10. Disbursement
app.include_router(disbursements_router)

# 11. Audit
app.include_router(audit_router)

# 12. Reconciliation
app.include_router(post_disbursement_router)

# 13. Repayment
app.include_router(repayments_router)

# 14. Collections
app.include_router(collections_router)

# 15. LMS
app.include_router(lms_router)



@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Credit Underwriting Platform",
        "version": "0.1.0",
    }