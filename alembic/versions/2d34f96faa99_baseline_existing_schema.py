"""baseline existing schema

Revision ID: 2d34f96faa99
Revises: 
Create Date: 2026-10-03 06:27:21.435282

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d34f96faa99'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Baseline existing database schema."""
    pass


def downgrade() -> None:
    """Baseline has no schema changes to reverse."""
    pass
