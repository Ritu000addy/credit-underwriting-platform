from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base

class LoanApplication(Base):
    __tablename__ = "loan_applications"

    application_id: Mapped[str] = mapped_column(
        String(50),
        primary_key = True,
    )

    customer_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("customers.customer_id"),
        nullable = False,
    )

    product: Mapped[str | None] = mapped_column(
        String(50),
        nullable = False,
    )

    requested_amount: Mapped[Decimal] = mapped_column(
        Numeric(15,2),
        nullable = False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable = False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default = datetime.utcnow,
        nullable = False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default = datetime.utcnow,
        onupdate = datetime.utcnow,
        nullable= False,
    )