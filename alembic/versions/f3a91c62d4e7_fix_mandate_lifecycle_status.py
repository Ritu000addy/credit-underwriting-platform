"""fix mandate lifecycle status

Revision ID: f3a91c62d4e7
Revises: e8c2b1a74f90
Create Date: 2026-10-05 23:05:26.776148

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f3a91c62d4e7'
down_revision: Union[str, Sequence[str], None] = 'e8c2b1a74f90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(
        "ck_mandates_status",
        "mandates",
        type_="check",
    )

    op.create_check_constraint(
        "ck_mandates_status",
        "mandates",
        "status IN ('CREATED', 'INITIATED', 'COMPLETED', 'FAILED')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ck_mandates_status",
        "mandates",
        type_="check",
    )

    op.create_check_constraint(
        "ck_mandates_status",
        "mandates",
        "status IN ('INITIATED', 'COMPLETED', 'FAILED')",
    )
