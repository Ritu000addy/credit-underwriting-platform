"""persist application loan terms

Revision ID: e0d3ef772f27
Revises: 7ac1e8b42f90
Create Date: 2026-10-12 20:07:19.047544

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e0d3ef772f27'
down_revision: Union[str, Sequence[str], None] = '7ac1e8b42f90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add persisted loan terms to existing applications."""
    op.add_column(
        "loan_applications",
        sa.Column("loan_tenure_months", sa.Integer(), nullable=True),
    )
    op.add_column(
        "loan_applications",
        sa.Column(
            "annual_interest_rate",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove persisted loan terms."""
    op.drop_column("loan_applications", "annual_interest_rate")
    op.drop_column("loan_applications", "loan_tenure_months")