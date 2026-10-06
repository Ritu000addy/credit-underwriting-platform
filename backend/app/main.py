import uuid
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from sqlalchemy.exc import IntegrityError

from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.core.exception_handlers import (
    integrity_error_handler,
    http_exception_handler,
    request_validation_exception_handler,
    unhandled_exception_handler,
)

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
# 7. MODEL GOVERNANCE
# ============================================================

from backend.app.api.routes.model_registry import (
    router as model_registry_router,
)
from backend.app.api.routes.policy_version import router as policy_version_router

# ============================================================
# 8. SANCTION
# ============================================================

from backend.app.api.routes.sanctions import router as sanctions_router


# ============================================================
# 9. AGREEMENT
# ============================================================

from backend.app.api.routes.agreements import router as agreements_router


# ============================================================
# 10. MANDATE
# ============================================================

from backend.app.api.routes.mandates import router as mandates_router


# ============================================================
# 11. DISBURSEMENT
# ============================================================

from backend.app.api.routes.disbursements import (
    router as disbursements_router,
)

# ============================================================
# 12. AUDIT
# ============================================================

from backend.app.api.routes.audit import router as audit_router

# ============================================================
# 13. RECONCILIATION
# ============================================================

from backend.app.api.routes.post_disbursement import (
    router as post_disbursement_router,
)

# ============================================================
# 14. REPAYMENT
# ============================================================

from backend.app.api.routes.repayments import router as repayments_router

# ============================================================
# 15. COLLECTIONS
# ============================================================

from backend.app.api.routes.collections import router as collections_router

# ============================================================
# 16. LMS
# ============================================================

from backend.app.api.routes.lms import router as lms_router

from backend.app.api.routes.auth import router as auth_router



app = FastAPI(
    title="AI Credit Underwriting Platform",
    description="GenAI-enabled credit underwriting and disbursement platform",
    version="0.1.0"
)

@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(
    request: Request,
    exc: RequestValidationError,
):
    return await request_validation_exception_handler(
        request,
        exc,
    )


@app.exception_handler(StarletteHTTPException)
async def handle_http_exception(
    request: Request,
    exc: StarletteHTTPException,
):
    return await http_exception_handler(
        request,
        exc,
    )


@app.exception_handler(IntegrityError)
async def handle_integrity_error(
    request: Request,
    exc: IntegrityError,
):
    return await integrity_error_handler(
        request,
        exc,
    )


@app.exception_handler(Exception)
async def handle_unhandled_exception(
    request: Request,
    exc: Exception,
):
    return await unhandled_exception_handler(
        request,
        exc,
    )

@app.middleware("http")
async def request_id_middleware(
    request: Request,
    call_next,
):
    request_id = request.headers.get(
        "X-Request-ID"
    )

    if not request_id:
        request_id = (
            f"REQ-{uuid.uuid4().hex[:12].upper()}"
        )

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


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

# 7. Model Governance
app.include_router(model_registry_router)

app.include_router(policy_version_router)

# 8. Sanction
app.include_router(sanctions_router)

# 9. Agreement
app.include_router(agreements_router)

# 10. Mandate
app.include_router(mandates_router)

# 11. Disbursement
app.include_router(disbursements_router)

# 12. Audit
app.include_router(audit_router)

# 13. Reconciliation
app.include_router(post_disbursement_router)

# 14. Repayment
app.include_router(repayments_router)

# 15. Collections
app.include_router(collections_router)

# 16. LMS
app.include_router(lms_router)

app.include_router(auth_router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Credit Underwriting Platform",
        "version": "0.1.0",
    }