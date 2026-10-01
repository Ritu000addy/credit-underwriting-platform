from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.app.models.bank_analysis import BankAnalysis
from backend.app.models.loan_application import LoanApplication
from backend.app.schemas.bank_analysis import BankAnalysisCreate


class BankAnalysisService:

    def create_analysis(
        self,
        db: Session,
        analysis: BankAnalysisCreate,
    ) -> BankAnalysis:

        application = db.get(
            LoanApplication,
            analysis.application_id,
        )

        if application is None:
            raise ValueError("APPLICATION_NOT_FOUND")

        bank_analysis = BankAnalysis(
            bank_analysis_id=f"BANK-{uuid4().hex[:12].upper()}",
            application_id=analysis.application_id,
            monthly_credits=analysis.monthly_credits,
            monthly_debits=analysis.monthly_debits,
            average_balance=analysis.average_balance,
            existing_emi=analysis.existing_emi,
            bounce_count=analysis.bounce_count,
            transactions_count=analysis.transactions_count,
            income_trend=analysis.income_trend,
            analysis_reference=analysis.analysis_reference,
            analyzed_at=datetime.utcnow(),
        )

        db.add(bank_analysis)
        db.commit()
        db.refresh(bank_analysis)

        return bank_analysis


bank_analysis_service = BankAnalysisService()