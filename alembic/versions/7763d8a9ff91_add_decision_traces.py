"""add decision traces

Revision ID: 7763d8a9ff91
Revises: 9546176c87dd
Create Date: 2026-10-05 10:17:46.510566

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "7763d8a9ff91"
down_revision: Union[str, Sequence[str], None] = "9546176c87dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Schema already exists in the deployed database."""
    pass


def downgrade() -> None:
    """Schema is managed by the existing baseline database."""
    pass