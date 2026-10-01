from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class BeneficiaryAccount(Base):
    __tablename__ = "beneficiary_accounts"

    beneficiary_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    application_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("loan_applications.application_id"),
        nullable=False,
    )

    account_holder_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    account_number_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    ifsc_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    bank_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    validation_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    validation_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    validated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )