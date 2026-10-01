from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base

class BureauReport(Base):
    __tablename__ = "bureau_reports"

    bureau_report_id: Mapped[str] = mapped_column(
        String(50),
        primary_key = True,
    )

    application_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("loan_applications.application_id"),
        nullable = False,
    )

    bureau_name: Mapped[str] = mapped_column(
        String(50),
        nullable = False,
    )

    bureau_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    dpd: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    active_loans: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    total_outstanding: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )

    write_offs: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )

    enquiries: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    report_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )