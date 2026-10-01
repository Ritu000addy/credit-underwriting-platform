from backend.app.api.routes import internal_history
from sqlalchemy.orm import Session

from backend.app.models.customer import Customer
from backend.app.models.loan_application import LoanApplication
from backend.app.models.bureau_report import BureauReport
from backend.app.models.bank_analysis import BankAnalysis
from backend.app.models.application_document import ApplicationDocument
from backend.app.models.employment import Employment
from backend.app.models.internal_history import InternalHistory
from backend.app.models.device_behaviour import DeviceBehaviour
from backend.app.models.document import Document
from backend.app.models.repayment_schedule import RepaymentSchedule
from backend.app.models.repayment import Repayment
from backend.app.models.collection import Collection

from backend.app.schemas.borrower360 import (
    Borrower360,
    KYCData,
    CreditBureauData,
    BankCashFlowData,
    EmploymentBusinessData,
    InternalHistoryData,
    DeviceBehaviourData,
    DocumentData,
)


class Borrower360Service:

    def build(
        self,
        db: Session,
        customer_id: str,
        application_id: str | None = None,
    ) -> Borrower360:

        customer = db.get(Customer, customer_id)

        if customer is None:
            raise ValueError("CUSTOMER_NOT_FOUND")

        application = None

        if application_id is not None:
            application = db.get(
                LoanApplication,
                application_id,
            )

            if application is None:
                raise ValueError("APPLICATION_NOT_FOUND")

            if application.customer_id != customer_id:
                raise ValueError("APPLICATION_CUSTOMER_MISMATCH")

        bureau = None
        bank = None
        employment = None
        internal_history = None
        device = None

        documents = []
        source_documents = []

        repayment_schedules = []
        repayments = []
        collections = []

        if application_id is not None:
            bureau = (
                db.query(BureauReport)
                .filter(
                    BureauReport.application_id == application_id
                )
                .order_by(BureauReport.fetched_at.desc())
                .first()
            )

            bank = (
                db.query(BankAnalysis)
                .filter(
                    BankAnalysis.application_id == application_id
                )
                .order_by(BankAnalysis.analyzed_at.desc())
                .first()
            )
        
            employment = (
                db.query(Employment)
                .filter(
                    Employment.application_id == application_id
                )
                .order_by(Employment.analyzed_at.desc())
                .first()
            )

            internal_history = (
                db.query(InternalHistory)
                .filter(
                    InternalHistory.application_id == application_id
                )
                .order_by(InternalHistory.analyzed_at.desc())
                .first()
            )
        
            device = (
                db.query(DeviceBehaviour)
                .filter(
                    DeviceBehaviour.application_id == application_id
                )
                .order_by(DeviceBehaviour.analyzed_at.desc())
                .first()
            )

            documents = (
                db.query(ApplicationDocument)
                .filter(
                    ApplicationDocument.application_id == application_id
                )
                .order_by(ApplicationDocument.created_at.asc())
                .all()
            )
        
            source_documents = (
                db.query(Document)
                .filter(
                    Document.application_id == application_id
                )
                .order_by(Document.created_at.asc())
                .all()
            )

            repayment_schedules = (
                db.query(RepaymentSchedule)
                .filter(
                    RepaymentSchedule.application_id == application_id
                )
                .order_by(
                    RepaymentSchedule.installment_number.asc()
                )
                .all()
            )

            repayments = (
                db.query(Repayment)
                .filter(
                    Repayment.application_id == application_id
                )
                .order_by(Repayment.created_at.asc())
                .all()
            )

            collections = (
                db.query(Collection)
                .filter(
                    Collection.application_id == application_id
                )
                .order_by(Collection.created_at.asc())
                .all()
            )

        return Borrower360(
            customer_id=customer.customer_id,

            kyc=KYCData(
                pan=customer.pan,
                aadhaar=customer.aadhaar_reference,
                aadhaar_kyc_status=customer.aadhaar_kyc_status,
                ekyc_result=customer.kyc_status,
                address= customer.address,
                dob= customer.dob,
            ),

            credit_bureau=(
                CreditBureauData(
                    score=bureau.bureau_score,
                    dpd=bureau.dpd,
                    enquiries=bureau.enquiries,
                    active_loans=bureau.active_loans,
                    total_outstanding=bureau.total_outstanding,
                    write_offs=bureau.write_offs,
                )
                if bureau is not None
                else None
            ),

            bank_cash_flow=(
                BankCashFlowData(
                    credits=bank.monthly_credits,
                    debits=bank.monthly_debits,
                    balance=bank.average_balance,
                    emi=bank.existing_emi,
                    bounce=bank.bounce_count,
                    transaction_count=bank.transactions_count,
                    income_pattern={
                        "income_trend": bank.income_trend,
                    }
                    if bank.income_trend is not None
                    else None,
                )
                if bank is not None
                else None
            ),

            employment_business=(
                EmploymentBusinessData(
                    salary=employment.monthly_income,
                    employer=employment.employer_name,
                    gst=(
                        str(employment.gst_registered)
                        if employment.gst_registered is not None
                        else None
                    ),
                    udyam=(
                        str(employment.udyam_registered)
                        if employment.udyam_registered is not None
                        else None
                    ),
                    business_vintage=employment.business_vintage_months,
                )
                if employment is not None
                else None
            ),

            internal_history=InternalHistoryData(
                past_loans=[
                    {
                        "previous_loans_count": (
                            internal_history.previous_loans_count
                        ),
                        "active_loans_count": (
                            internal_history.active_loans_count
                        ),
                        "closed_loans_count": (
                            internal_history.closed_loans_count
                        ),
                        "total_previous_exposure": (
                            internal_history.total_previous_exposure
                        ),
                        "total_outstanding_amount": (
                            internal_history.total_outstanding_amount
                        ),
                    }
                ]
                if internal_history is not None
                else [],

                repayment=[
                    {
                        "repayment_id": repayment.repayment_id,
                        "repayment_schedule_id": (
                            repayment.repayment_schedule_id
                        ),
                        "amount": repayment.repayment_amount,
                        "status": repayment.status,
                        "paid_at": repayment.paid_at,
                    }
                    for repayment in repayments
                ],

                dpd=(
                    [
                        {
                            "repayment_schedule_id": (
                                collection.repayment_schedule_id
                            ),
                            "days_past_due": collection.days_past_due,
                            "status": collection.status,
                        }
                        for collection in collections
                        if collection.repayment_schedule_id is not None
                    ]
                    +
                    (
                        [
                            {
                                "dpd_count": internal_history.dpd_count,
                                "max_dpd": internal_history.max_dpd,
                            }
                        ]
                        if internal_history is not None
                        else []
                    )
                ),

                collections=(
                    [
                        {
                            "collection_id": collection.collection_id,
                            "repayment_schedule_id": (
                                collection.repayment_schedule_id
                            ),
                            "collection_type": collection.collection_type,
                            "due_amount": collection.due_amount,
                            "collected_amount": (
                                collection.collected_amount
                            ),
                            "outstanding_amount": (
                                collection.outstanding_amount
                            ),
                            "days_past_due": (
                                collection.days_past_due
                            ),
                            "status": collection.status,
                        }
                        for collection in collections
                    ]
                    +
                    (
                        [
                            {
                                "overdue_amount": (
                                    internal_history.overdue_amount
                                ),
                                "write_off_count": (
                                    internal_history.write_off_count
                                ),
                                "settlement_count": (
                                    internal_history.settlement_count
                                ),
                            }
                        ]
                        if internal_history is not None
                        else []
                    )
                ),
            ),
            device_behaviour=(
                DeviceBehaviourData(
                    device=device.device_id,
                    ip=device.ip_address,
                    velocity={
                        "application_velocity": (
                            device.application_velocity
                        ),
                        "device_velocity": (
                            device.device_velocity
                        ),
                        "ip_velocity": device.ip_velocity,
                    },
                    session_patterns={
                        "login_count": device.login_count,
                        "session_count": device.session_count,
                        "failed_login_count": (
                            device.failed_login_count
                        ),
                        "device_age_days": device.device_age_days,
                        "behavioural_risk_score": (
                            device.behavioural_risk_score
                        ),
                        "fraud_indicator": device.fraud_indicator,
                    },
                )
                if device is not None
                else None
            ),

            documents=DocumentData(
                payslips=[
                    {
                        "document_id": document.document_id,
                        "document_type": document.document_type,
                        "verification_status": (
                            document.verification_status
                        ),
                        "document_reference": (
                            document.document_reference
                        ),
                        "document_name": document.document_name,
                        "extracted_data": document.extracted_data,
                    }
                    for document in documents
                    if document.document_type.upper() == "PAYSLIP"
                ]
                +
                [
                    {
                        "document_id": document.document_id,
                        "document_type": document.document_type,
                        "verification_status": (
                            document.verification_status
                        ),
                        "document_reference": (
                            document.document_reference
                        ),
                        "document_name": document.document_name,
                        "extracted_data": document.extracted_data,
                    }
                    for document in source_documents
                    if document.document_type.upper() == "PAYSLIP"
                ],

                bank_statements=[
                    {
                        "document_id": document.document_id,
                        "document_type": document.document_type,
                        "verification_status": (
                            document.verification_status
                        ),
                        "document_reference": (
                            document.document_reference
                        ),
                        "document_name": document.document_name,
                        "extracted_data": document.extracted_data,
                    }
                    for document in documents
                    if document.document_type.upper()
                    == "BANK_STATEMENT"
                ]
                +
                [
                    {
                        "document_id": document.document_id,
                        "document_type": document.document_type,
                        "verification_status": (
                            document.verification_status
                        ),
                        "document_reference": (
                            document.document_reference
                        ),
                        "document_name": document.document_name,
                        "extracted_data": document.extracted_data,
                    }
                    for document in source_documents
                    if document.document_type.upper()
                    == "BANK_STATEMENT"
                ],

                invoices=[
                    {
                        "document_id": document.document_id,
                        "document_type": document.document_type,
                        "verification_status": (
                            document.verification_status
                        ),
                        "document_reference": (
                            document.document_reference
                        ),
                        "document_name": document.document_name,
                        "extracted_data": document.extracted_data,
                    }
                    for document in documents
                    if document.document_type.upper() == "INVOICE"
                ]
                +
                [
                    {
                        "document_id": document.document_id,
                        "document_type": document.document_type,
                        "verification_status": (
                            document.verification_status
                        ),
                        "document_reference": (
                            document.document_reference
                        ),
                        "document_name": document.document_name,
                        "extracted_data": document.extracted_data,
                    }
                    for document in source_documents
                    if document.document_type.upper() == "INVOICE"
                ],
        
                business_proofs=[
                    {
                        "document_id": document.document_id,
                        "document_type": document.document_type,
                        "verification_status": (
                            document.verification_status
                        ),
                        "document_reference": (
                            document.document_reference
                        ),
                    }
                    for document in documents
                    if document.document_type.upper()
                    == "BUSINESS_PROOF"
                ]
                +
                [
                    {
                        "document_id": document.document_id,
                        "document_type": document.document_type,
                        "verification_status": (
                            document.verification_status
                        ),
                        "document_reference": (
                            document.document_reference
                        ),
                        "document_name": document.document_name,
                        "extracted_data": document.extracted_data,
                    }
                    for document in source_documents
                    if document.document_type.upper()
                    == "BUSINESS_PROOF"
                ],
            )
            if documents or source_documents
            else None,
        )

borrower360_service = Borrower360Service()