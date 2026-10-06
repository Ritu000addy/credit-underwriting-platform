"""harden reconciliation workflow integrity

Revision ID: c6e18a4b903f
Revises: b7c42e91d583
Create Date: 2026-10-05 23:46:28.991634

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c6e18a4b903f'
down_revision: Union[str, Sequence[str], None] = 'b7c42e91d583'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "ck_reconciliation_transaction_type",
        "reconciliation",
        "transaction_type IN ('DISBURSEMENT', 'REPAYMENT')",
    )

    op.create_check_constraint(
        "ck_reconciliation_status",
        "reconciliation",
        "reconciliation_status IN "
        "('PENDING', 'MATCHED', 'MISMATCH', 'CLOSED')",
    )

    op.create_check_constraint(
        "ck_operations_queue_status",
        "operations_queue",
        "queue_status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED')",
    )

    op.create_check_constraint(
        "ck_operations_queue_type",
        "operations_queue",
        "queue_type IN ('RECONCILIATION_MISMATCH')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ck_operations_queue_type",
        "operations_queue",
        type_="check",
    )

    op.drop_constraint(
        "ck_operations_queue_status",
        "operations_queue",
        type_="check",
    )

    op.drop_constraint(
        "ck_reconciliation_status",
        "reconciliation",
        type_="check",
    )

    op.drop_constraint(
        "ck_reconciliation_transaction_type",
        "reconciliation",
        type_="check",
    )
