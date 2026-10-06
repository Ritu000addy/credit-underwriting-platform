"""add repayment status integrity

Revision ID: a4d71e9c2f63
Revises: f3a91c62d4e7
Create Date: 2026-10-05 23:13:32.170239

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a4d71e9c2f63'
down_revision: Union[str, Sequence[str], None] = 'f3a91c62d4e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "ck_repayments_status",
        "repayments",
        "status IN ('SUCCESS')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ck_repayments_status",
        "repayments",
        type_="check",
    )