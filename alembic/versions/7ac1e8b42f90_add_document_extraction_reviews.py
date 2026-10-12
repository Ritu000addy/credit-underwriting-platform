"""add document extraction review tasks"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7ac1e8b42f90"
down_revision: Union[str, Sequence[str], None] = "9e7e2d5283af"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_extraction_reviews",
        sa.Column("review_id", sa.String(50), primary_key=True),
        sa.Column(
            "document_id",
            sa.String(50),
            sa.ForeignKey("documents.document_id"),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            sa.String(50),
            sa.ForeignKey("loan_applications.application_id"),
            nullable=False,
        ),
        sa.Column("analysis_reference", sa.String(500), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("extraction_snapshot", sa.Text(), nullable=False),
        sa.Column(
            "assigned_reviewer_id",
            sa.String(50),
            sa.ForeignKey("auth_users.user_id"),
            nullable=True,
        ),
        sa.Column(
            "assigned_by_user_id",
            sa.String(50),
            sa.ForeignKey("auth_users.user_id"),
            nullable=True,
        ),
        sa.Column("assigned_at", sa.DateTime(), nullable=True),
        sa.Column(
            "reviewed_by_user_id",
            sa.String(50),
            sa.ForeignKey("auth_users.user_id"),
            nullable=True,
        ),
        sa.Column("accepted_fields", sa.Text(), nullable=True),
        sa.Column("accepted_values", sa.Text(), nullable=True),
        sa.Column("acknowledged_conflicts", sa.Text(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'IN_REVIEW', 'APPROVED', 'REJECTED')",
            name="ck_document_extraction_reviews_status",
        ),
        sa.UniqueConstraint(
            "analysis_reference",
            name="uq_document_extraction_reviews_analysis_reference",
        ),
    )

    op.create_index(
        "ix_document_extraction_reviews_application_status",
        "document_extraction_reviews",
        ["application_id", "status"],
        unique=False,
    )

    op.create_index(
        "ix_document_extraction_reviews_assignee_status",
        "document_extraction_reviews",
        ["assigned_reviewer_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_extraction_reviews_assignee_status",
        table_name="document_extraction_reviews",
    )
    op.drop_index(
        "ix_document_extraction_reviews_application_status",
        table_name="document_extraction_reviews",
    )
    op.drop_table("document_extraction_reviews")