from decimal import Decimal

from pydantic import BaseModel


class BureauReportCreate(BaseModel):
    application_id: str
    bureau_name: str
    bureau_score: int | None = None
    dpd: int | None = None
    active_loans: int | None = None
    total_outstanding: Decimal | None = None
    write_offs: Decimal | None = None
    enquiries: int | None = None
    report_reference: str | None = None