"""add source evidence verification status

Revision ID: 0fc85844eba3
Revises: e0d3ef772f27
Create Date: 2026-10-13 09:45:16.121600

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0fc85844eba3'
down_revision: Union[str, Sequence[str], None] = 'e0d3ef772f27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "bureau_reports",
        sa.Column(
            "verification_status",
            sa.String(length=20),
            server_default="UNVERIFIED",
            nullable=False,
        ),
    )
    op.add_column(
        "bank_analysis",
        sa.Column(
            "verification_status",
            sa.String(length=20),
            server_default="UNVERIFIED",
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("bank_analysis", "verification_status")
    op.drop_column("bureau_reports", "verification_status")
