from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models.customer import Customer
from backend.app.models.loan_application import LoanApplication
from backend.app.schemas.application import ApplicationCreate


class ApplicationService:

    def create_application(
        self,
        db: Session,
        application: ApplicationCreate,
    ) -> LoanApplication:

        customer = db.get(
            Customer,
            application.customer_id,
        )

        if customer is None:
            raise ValueError("CUSTOMER_NOT_FOUND")

        existing_application = db.get(
            LoanApplication,
            application.application_id,
        )

        if existing_application is not None:
            raise ValueError("APPLICATION_ALREADY_EXISTS")

        loan_application = LoanApplication(
            application_id=application.application_id,
            customer_id=application.customer_id,
            product="UNSPECIFIED",
            requested_amount=Decimal(str(application.requested_amount)),
            status="RECEIVED",
        )

        db.add(loan_application)

        db.commit()
        db.refresh(loan_application)

        return loan_application

    def get_application(
        self,
        db: Session,
        application_id: str,
    ) -> LoanApplication | None:

        return db.get(
            LoanApplication,
            application_id,
        )


application_service = ApplicationService()