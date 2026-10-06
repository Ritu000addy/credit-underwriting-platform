"""harden collection status integrity

Revision ID: b7c42e91d583
Revises: a4d71e9c2f63
Create Date: 2026-10-05 23:26:53.204894

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b7c42e91d583'
down_revision: Union[str, Sequence[str], None] = 'a4d71e9c2f63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "ck_collections_status",
        "collections",
        "status IN ('PENDING', 'PARTIAL', 'COLLECTED')",
    )

    op.create_check_constraint(
        "ck_collections_pending_status_consistency",
        "collections",
        "status <> 'PENDING' "
        "OR (collected_amount = 0 AND outstanding_amount = due_amount)",
    )

    op.create_check_constraint(
        "ck_collections_collected_status_consistency",
        "collections",
        "status <> 'COLLECTED' OR outstanding_amount = 0",
    )

    op.create_check_constraint(
        "ck_collections_partial_status_consistency",
        "collections",
        "status <> 'PARTIAL' OR outstanding_amount > 0",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ck_collections_partial_status_consistency",
        "collections",
        type_="check",
    )

    op.drop_constraint(
        "ck_collections_collected_status_consistency",
        "collections",
        type_="check",
    )

    op.drop_constraint(
        "ck_collections_pending_status_consistency",
        "collections",
        type_="check",
    )

    op.drop_constraint(
        "ck_collections_status",
        "collections",
        type_="check",
    )