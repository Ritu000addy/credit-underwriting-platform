"""add auth users

Revision ID: 20b10789ba16
Revises: d1a74c9e5286
Create Date: 2026-10-06 03:01:31.194483

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20b10789ba16'
down_revision: Union[str, Sequence[str], None] = 'd1a74c9e5286'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "auth_users",
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("full_name", sa.String(length=150), nullable=True),
        sa.Column("hashed_password", sa.Text(), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "role IN ('ADMIN', 'CREDIT_ANALYST', 'CREDIT_OFFICER', "
            "'OPERATIONS', 'RISK', 'AUDITOR')",
            name="ck_auth_users_role",
        ),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )

    op.create_index(
        "ix_auth_users_username",
        "auth_users",
        ["username"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_auth_users_username",
        table_name="auth_users",
    )
    op.drop_table("auth_users")