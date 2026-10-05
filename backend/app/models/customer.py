from datetime import datetime, date

from sqlalchemy import DateTime, String, Date, Index
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base

class Customer(Base):
    __tablename__ = "customers"

    __table_args__ = (
        Index(
            "ix_customers_pan",
            "pan",
        ),
    )

    customer_id: Mapped[str] = mapped_column(
        String(50),
        primary_key = True,
    )

    kyc_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable = True,
    )

    pan: Mapped[str | None] = mapped_column(
        String(10),
        nullable = True,
    )

    aadhaar_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable = True,
    )

    aadhaar_kyc_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    dob: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default = datetime.utcnow,
        nullable= False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default = datetime.utcnow,
        onupdate = datetime.utcnow,
        nullable= False,
    )