"""add model governance metadata

Revision ID: ee023ad3f766
Revises: e20661ef7dd4
Create Date: 2026-10-05 12:23:19.166869

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee023ad3f766'
down_revision: Union[str, Sequence[str], None] = 'e20661ef7dd4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "model_registry",
        sa.Column(
            "lifecycle_status",
            sa.String(length=30),
            nullable=True,
        ),
    )

    op.add_column(
        "model_registry",
        sa.Column(
            "validation_status",
            sa.String(length=30),
            nullable=True,
        ),
    )

    op.add_column(
        "model_registry",
        sa.Column(
            "validation_date",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.add_column(
        "model_registry",
        sa.Column(
            "validated_by",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "model_registry",
        sa.Column(
            "validation_notes",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "model_registry",
        sa.Column(
            "approval_date",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.add_column(
        "model_registry",
        sa.Column(
            "approved_by",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "model_registry",
        sa.Column(
            "rollback_of_version",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "model_registry",
        sa.Column(
            "governance_notes",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "model_registry",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE model_registry
        SET lifecycle_status = 'REGISTERED'
        WHERE lifecycle_status IS NULL
        """
    )

    op.execute(
        """
        UPDATE model_registry
        SET validation_status = 'NOT_VALIDATED'
        WHERE validation_status IS NULL
        """
    )

    op.execute(
        """
        UPDATE model_registry
        SET updated_at = created_at
        WHERE updated_at IS NULL
        """
    )

    op.alter_column(
        "model_registry",
        "lifecycle_status",
        nullable=False,
        server_default=sa.text("'REGISTERED'"),
    )

    op.alter_column(
        "model_registry",
        "validation_status",
        nullable=False,
        server_default=sa.text("'NOT_VALIDATED'"),
    )

    op.create_check_constraint(
        "ck_model_registry_lifecycle_status",
        "model_registry",
        (
            "lifecycle_status IN "
            "('REGISTERED', 'VALIDATION', 'APPROVED', 'ACTIVE', "
            "'INACTIVE', 'ROLLED_BACK', 'REJECTED')"
        ),
    )

    op.create_check_constraint(
        "ck_model_registry_validation_status",
        "model_registry",
        (
            "validation_status IN "
            "('NOT_VALIDATED', 'IN_PROGRESS', 'PASSED', 'FAILED')"
        ),
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_model_registry_validation_status",
        "model_registry",
        type_="check",
    )

    op.drop_constraint(
        "ck_model_registry_lifecycle_status",
        "model_registry",
        type_="check",
    )

    op.drop_column("model_registry", "updated_at")
    op.drop_column("model_registry", "governance_notes")
    op.drop_column("model_registry", "rollback_of_version")
    op.drop_column("model_registry", "approved_by")
    op.drop_column("model_registry", "approval_date")
    op.drop_column("model_registry", "validation_notes")
    op.drop_column("model_registry", "validated_by")
    op.drop_column("model_registry", "validation_date")
    op.drop_column("model_registry", "validation_status")
    op.drop_column("model_registry", "lifecycle_status")