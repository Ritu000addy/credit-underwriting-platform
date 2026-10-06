"""add missing cross entity foreign keys

Revision ID: d1a74c9e5286
Revises: c6e18a4b903f
Create Date: 2026-10-05 23:57:07.432215

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd1a74c9e5286'
down_revision: Union[str, Sequence[str], None] = 'c6e18a4b903f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_foreign_key(
        "fk_credit_policy_rules_policy_version",
        "credit_policy_rules",
        "policy_versions",
        ["policy_version"],
        ["policy_version"],
    )

    op.create_foreign_key(
        "fk_operations_queue_reconciliation",
        "operations_queue",
        "reconciliation",
        ["reconciliation_id"],
        ["reconciliation_id"],
    )

    op.create_foreign_key(
        "fk_operations_queue_disbursement",
        "operations_queue",
        "disbursements",
        ["disbursement_id"],
        ["disbursement_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_operations_queue_disbursement",
        "operations_queue",
        type_="foreignkey",
    )

    op.drop_constraint(
        "fk_operations_queue_reconciliation",
        "operations_queue",
        type_="foreignkey",
    )

    op.drop_constraint(
        "fk_credit_policy_rules_policy_version",
        "credit_policy_rules",
        type_="foreignkey",
    )