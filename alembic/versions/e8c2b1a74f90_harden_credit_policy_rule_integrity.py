"""harden credit policy rule integrity

Revision ID: e8c2b1a74f90
Revises: d7fe11c759ad
Create Date: 2026-10-05 21:53:33.029904

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e8c2b1a74f90'
down_revision: Union[str, Sequence[str], None] = 'd7fe11c759ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        "uq_credit_policy_rule_policy_version_rule_code",
        "credit_policy_rules",
        ["policy_version", "rule_code"],
    )

    op.create_check_constraint(
        "ck_credit_policy_rule_effective_dates",
        "credit_policy_rules",
        "effective_to IS NULL "
        "OR effective_from IS NULL "
        "OR effective_to >= effective_from",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ck_credit_policy_rule_effective_dates",
        "credit_policy_rules",
        type_="check",
    )

    op.drop_constraint(
        "uq_credit_policy_rule_policy_version_rule_code",
        "credit_policy_rules",
        type_="unique",
    )