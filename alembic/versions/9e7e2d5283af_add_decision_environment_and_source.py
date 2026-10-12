"""add decision environment and source

Revision ID: 9e7e2d5283af
Revises: a1b2c3d4e5f6
Create Date: 2026-10-09 23:10:10.623833

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e7e2d5283af'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "credit_decisions",
        sa.Column("execution_environment", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "credit_decisions",
        sa.Column("record_source", sa.String(length=30), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column(
        "credit_decisions", 
        "record_source")
    op.drop_column(
        "credit_decisions", 
        "execution_environment")
