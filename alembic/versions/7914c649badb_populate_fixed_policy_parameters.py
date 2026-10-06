"""populate fixed policy parameters

Revision ID: 7914c649badb
Revises: 20b10789ba16
Create Date: 2026-10-06 09:47:20.765695

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7914c649badb'
down_revision: Union[str, Sequence[str], None] = '20b10789ba16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    result = bind.execute(
        sa.text(
            """
            UPDATE credit_policy_rules
            SET rule_parameters = CAST(
                :rule_parameters AS JSONB
            )
            WHERE policy_version = :policy_version
              AND rule_code = :rule_code
            """
        ),
        {
            "rule_parameters": (
                '{'
                '"pan_required": true,'
                '"ekyc_required": true,'
                '"required_ekyc_result": "VERIFIED",'
                '"aadhaar_kyc_required": false,'
                '"policy_source": "COMPANY_FIXED_POLICY"'
                '}'
            ),
            "policy_version": "POL-2026.09",
            "rule_code": "KYC_BANK_VALIDATION",
        },
    )

    if result.rowcount != 1:
        raise RuntimeError(
            "EXPECTED_ONE_KYC_POLICY_RULE_TO_UPDATE"
        )    


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()

    bind.execute(
        sa.text(
            """
            UPDATE credit_policy_rules
            SET rule_parameters = CAST(
                :rule_parameters AS JSONB
            )
            WHERE policy_version = :policy_version
              AND rule_code = :rule_code
            """
        ),
        {
            "rule_parameters": "{}",
            "policy_version": "POL-2026.09",
            "rule_code": "KYC_BANK_VALIDATION",
        },
    )
