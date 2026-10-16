
"""Add persistent GenAI generation history.

Revision ID: 6a91c2d8f740
Revises: 3edffe83bce3
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "6a91c2d8f740"
down_revision = "3edffe83bce3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "genai_generation_history",
        sa.Column(
            "generation_id",
            sa.String(length=50),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "application_id",
            sa.String(length=50),
            sa.ForeignKey(
                "loan_applications.application_id",
                ondelete="SET NULL",
            ),
            nullable=True,
        ),
        sa.Column(
            "generation_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=50), nullable=True),
        sa.Column("model_name", sa.String(length=150), nullable=True),
        sa.Column("model_version", sa.String(length=100), nullable=True),
        sa.Column("prompt_version", sa.String(length=100), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column(
            "validation_status",
            sa.String(length=30),
            nullable=True,
        ),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column(
            "request_reference",
            sa.String(length=150),
            nullable=True,
        ),
        sa.Column(
            "generation_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_genai_history_application_created",
        "genai_generation_history",
        ["application_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_genai_history_application_created",
        table_name="genai_generation_history",
    )
    op.drop_table("genai_generation_history")
