"""add maker checker manual review

Revision ID: e20661ef7dd4
Revises: 78382ad65e30
Create Date: 2026-10-05 11:23:59.027358

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e20661ef7dd4"
down_revision: Union[str, Sequence[str], None] = "78382ad65e30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ------------------------------------------------------------
    # Remove old constraints
    # ------------------------------------------------------------

    op.drop_constraint(
        "ck_manual_reviews_status",
        "manual_reviews",
        type_="check",
    )

    op.drop_constraint(
        "ck_manual_reviews_completed_decision",
        "manual_reviews",
        type_="check",
    )

    # ------------------------------------------------------------
    # Add maker-checker fields
    # ------------------------------------------------------------

    op.add_column(
        "manual_reviews",
        sa.Column(
            "checker_id",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "manual_reviews",
        sa.Column(
            "checker_decision",
            sa.String(length=30),
            nullable=True,
        ),
    )

    op.add_column(
        "manual_reviews",
        sa.Column(
            "checker_remarks",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "manual_reviews",
        sa.Column(
            "checker_completed_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    # ------------------------------------------------------------
    # Add maker-checker control flag
    # ------------------------------------------------------------

    op.add_column(
        "manual_reviews",
        sa.Column(
            "maker_checker_required",
            sa.Boolean(),
            nullable=True,
        ),
    )

    # Existing completed reviews were created before
    # maker-checker existed, so preserve them as legacy reviews.
    op.execute(
        """
        UPDATE manual_reviews
        SET maker_checker_required = false
        WHERE maker_checker_required IS NULL
        """
    )

    # All new reviews require maker-checker by default.
    op.alter_column(
        "manual_reviews",
        "maker_checker_required",
        nullable=False,
        server_default=sa.text("true"),
    )

    # ------------------------------------------------------------
    # Index
    # ------------------------------------------------------------

    op.create_index(
        "ix_manual_reviews_checker_id",
        "manual_reviews",
        ["checker_id"],
        unique=False,
    )

    # ------------------------------------------------------------
    # Workflow/status constraints
    # ------------------------------------------------------------

    op.create_check_constraint(
        "ck_manual_reviews_status",
        "manual_reviews",
        (
            "review_status IN "
            "('OPEN', 'IN_PROGRESS', 'PENDING_CHECKER', 'COMPLETED')"
        ),
    )

    op.create_check_constraint(
        "ck_manual_reviews_checker_decision",
        "manual_reviews",
        (
            "checker_decision IS NULL "
            "OR checker_decision IN ('APPROVE', 'REJECT')"
        ),
    )

    op.create_check_constraint(
        "ck_manual_reviews_pending_checker",
        "manual_reviews",
        (
            "review_status <> 'PENDING_CHECKER' "
            "OR (reviewer_id IS NOT NULL "
            "AND reviewer_decision IS NOT NULL)"
        ),
    )

    op.create_check_constraint(
        "ck_manual_reviews_completed_checker_decision",
        "manual_reviews",
        (
            "review_status <> 'COMPLETED' "
            "OR maker_checker_required = false "
            "OR checker_decision IS NOT NULL"
        ),
    )

    op.create_check_constraint(
        "ck_manual_reviews_maker_checker_separation",
        "manual_reviews",
        (
            "checker_id IS NULL "
            "OR checker_id <> reviewer_id"
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    # ------------------------------------------------------------
    # Remove maker-checker constraints
    # ------------------------------------------------------------

    op.drop_constraint(
        "ck_manual_reviews_maker_checker_separation",
        "manual_reviews",
        type_="check",
    )

    op.drop_constraint(
        "ck_manual_reviews_completed_checker_decision",
        "manual_reviews",
        type_="check",
    )

    op.drop_constraint(
        "ck_manual_reviews_pending_checker",
        "manual_reviews",
        type_="check",
    )

    op.drop_constraint(
        "ck_manual_reviews_checker_decision",
        "manual_reviews",
        type_="check",
    )

    op.drop_constraint(
        "ck_manual_reviews_status",
        "manual_reviews",
        type_="check",
    )

    # ------------------------------------------------------------
    # Restore original constraints
    # ------------------------------------------------------------

    op.create_check_constraint(
        "ck_manual_reviews_status",
        "manual_reviews",
        (
            "review_status IN "
            "('OPEN', 'IN_PROGRESS', 'COMPLETED')"
        ),
    )

    op.create_check_constraint(
        "ck_manual_reviews_completed_decision",
        "manual_reviews",
        (
            "review_status <> 'COMPLETED' "
            "OR reviewer_decision IS NOT NULL"
        ),
    )

    # ------------------------------------------------------------
    # Remove index
    # ------------------------------------------------------------

    op.drop_index(
        "ix_manual_reviews_checker_id",
        table_name="manual_reviews",
    )

    # ------------------------------------------------------------
    # Remove columns
    # ------------------------------------------------------------

    op.drop_column(
        "manual_reviews",
        "maker_checker_required",
    )

    op.drop_column(
        "manual_reviews",
        "checker_completed_at",
    )

    op.drop_column(
        "manual_reviews",
        "checker_remarks",
    )

    op.drop_column(
        "manual_reviews",
        "checker_decision",
    )

    op.drop_column(
        "manual_reviews",
        "checker_id",
    )