"""add policy version governance

Revision ID: 409f735538f1
Revises: a31d01d566a0
Create Date: 2026-10-05 14:30:37.623125

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '409f735538f1'
down_revision: Union[str, Sequence[str], None] = 'a31d01d566a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("policy_versions"):
        return

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

    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("policy_versions"):
        op.drop_table("policy_versions")