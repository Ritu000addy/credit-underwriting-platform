from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base

class BureauReport(Base):
    __tablename__ = "bureau_reports"

    __table_args__ = (
        Index(
            "ix_bureau_reports_application_fetched",
            "application_id",
            "fetched_at",
        ),
        CheckConstraint(
            "dpd IS NULL OR dpd >= 0",
            name="ck_bureau_reports_dpd_non_negative",
        ),
        CheckConstraint(
            "active_loans IS NULL OR active_loans >= 0",
            name="ck_bureau_reports_active_loans_non_negative",
        ),
        CheckConstraint(
            "total_outstanding IS NULL OR total_outstanding >= 0",
            name="ck_bureau_reports_total_outstanding_non_negative",
        ),
        CheckConstraint(
            "write_offs IS NULL OR write_offs >= 0",
            name="ck_bureau_reports_write_offs_non_negative",
        ),
        CheckConstraint(
            "enquiries IS NULL OR enquiries >= 0",
            name="ck_bureau_reports_enquiries_non_negative",
        ),
    )

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