"""link sanctions to credit decisions

Revision ID: 3edffe83bce3
Revises: 1f76ee173b64
Create Date: 2026-10-15 12:12:30.659745

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3edffe83bce3'
down_revision: Union[str, Sequence[str], None] = '1f76ee173b64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Link sanctions to their authorizing credit decisions."""
    op.add_column(
        "sanctions",
        sa.Column("decision_id", sa.String(length=50), nullable=True),
    )
    op.create_foreign_key(
        "fk_sanctions_decision_id_credit_decisions",
        "sanctions",
        "credit_decisions",
        ["decision_id"],
        ["decision_id"],
        ondelete="RESTRICT",
    )

    op.create_index(
        "ix_sanctions_decision_id",
        "sanctions",
        ["decision_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the sanction-to-decision link."""
    op.drop_index(
        "ix_sanctions_decision_id",
        table_name="sanctions",
    )

    op.drop_constraint(
        "fk_sanctions_decision_id_credit_decisions",
        "sanctions",
        type_="foreignkey",
    )

    op.drop_column("sanctions", "decision_id")