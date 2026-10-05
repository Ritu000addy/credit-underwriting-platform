"""harden beneficiary account integrity

Revision ID: 8b21df9aae73
Revises: 030557b0ceb7
Create Date: 2026-10-05 03:37:57.269136

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b21df9aae73'
down_revision: Union[str, Sequence[str], None] = '030557b0ceb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        "ix_beneficiary_accounts_application",
        "beneficiary_accounts",
        ["application_id"],
        unique=False,
    )

    op.create_check_constraint(
        "ck_beneficiary_accounts_validation_status",
        "beneficiary_accounts",
        "validation_status IN ('PENDING', 'VALIDATED', 'FAILED')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ck_beneficiary_accounts_validation_status",
        "beneficiary_accounts",
        type_="check",
    )

    op.drop_index(
        "ix_beneficiary_accounts_application",
        table_name="beneficiary_accounts",
    )
