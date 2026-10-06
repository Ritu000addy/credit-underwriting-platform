"""add policy version governance

Revision ID: a31d01d566a0
Revises: ee023ad3f766
Create Date: 2026-10-05 14:28:45.237429

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a31d01d566a0'
down_revision: Union[str, Sequence[str], None] = 'ee023ad3f766'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "policy_versions",
        sa.Column(
            "policy_version_id",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "policy_version",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "effective_from",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "effective_to",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column(
            "policy_reference",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column(
            "governance_notes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "policy_version_id",
        ),
        sa.UniqueConstraint(
            "policy_version",
            name="uq_policy_versions_policy_version",
        ),
        sa.CheckConstraint(
            "status IN "
            "('DRAFT', 'ACTIVE', 'INACTIVE', 'ROLLED_BACK', 'RETIRED')",
            name="ck_policy_versions_status",
        ),
        sa.CheckConstraint(
            "effective_to IS NULL "
            "OR effective_to >= effective_from",
            name="ck_policy_versions_effective_dates",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("policy_versions")