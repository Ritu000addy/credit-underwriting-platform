"""add policy rule parameters

Revision ID: d7fe11c759ad
Revises: 409f735538f1
Create Date: 2026-10-05 14:35:36.908280

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd7fe11c759ad'
down_revision: Union[str, Sequence[str], None] = '409f735538f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
    "credit_policy_rules",
    sa.Column(
        "rule_parameters",
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
    ),
)


def downgrade() -> None:
    """Downgrade schema."""
    pass
