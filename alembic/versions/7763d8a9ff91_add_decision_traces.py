"""add decision traces

Revision ID: 7763d8a9ff91
Revises: 9546176c87dd
Create Date: 2026-10-05 10:17:46.510566

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "7763d8a9ff91"
down_revision: Union[str, Sequence[str], None] = "9546176c87dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create underwriting feature snapshots and decision traces."""

    op.create_table(
        "underwriting_feature_snapshots",
        sa.Column(
            "feature_snapshot_id",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "decision_id",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "model_version",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "feature_version",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "features",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["loan_applications.application_id"],
            name="underwriting_feature_snapshots_application_id_fkey",
        ),
        sa.ForeignKeyConstraint(
            ["decision_id"],
            ["credit_decisions.decision_id"],
            name="underwriting_feature_snapshots_decision_id_fkey",
        ),
        sa.PrimaryKeyConstraint(
            "feature_snapshot_id",
            name="underwriting_feature_snapshots_pkey",
        ),
        sa.UniqueConstraint(
            "decision_id",
            name="uq_underwriting_feature_snapshots_decision_id",
        ),
    )

    op.create_index(
        "ix_underwriting_feature_snapshots_application_created",
        "underwriting_feature_snapshots",
        ["application_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "decision_traces",
        sa.Column(
            "trace_id",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "decision_id",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "feature_snapshot_id",
            sa.String(length=50),
            nullable=True,
        ),
        sa.Column(
            "decision",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "model_version",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "policy_version",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "effective_from",
            sa.String(length=20),
            nullable=True,
        ),
        sa.Column(
            "effective_to",
            sa.String(length=20),
            nullable=True,
        ),
        sa.Column(
            "model_outputs",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "policy_evaluation",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "reason_codes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "decision_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["loan_applications.application_id"],
            name="decision_traces_application_id_fkey",
        ),
        sa.ForeignKeyConstraint(
            ["decision_id"],
            ["credit_decisions.decision_id"],
            name="decision_traces_decision_id_fkey",
        ),
        sa.ForeignKeyConstraint(
            ["feature_snapshot_id"],
            ["underwriting_feature_snapshots.feature_snapshot_id"],
            name="decision_traces_feature_snapshot_id_fkey",
        ),
        sa.PrimaryKeyConstraint(
            "trace_id",
            name="decision_traces_pkey",
        ),
        sa.UniqueConstraint(
            "decision_id",
            name="uq_decision_traces_decision_id",
        ),
    )

    op.create_index(
        "ix_decision_traces_application_created",
        "decision_traces",
        ["application_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop decision traces and underwriting feature snapshots."""

    op.drop_index(
        "ix_decision_traces_application_created",
        table_name="decision_traces",
    )

    op.drop_table("decision_traces")

    op.drop_index(
        "ix_underwriting_feature_snapshots_application_created",
        table_name="underwriting_feature_snapshots",
    )

    op.drop_table("underwriting_feature_snapshots")