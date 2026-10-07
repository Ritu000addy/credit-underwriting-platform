"""populate fixed policy parameters

Revision ID: 7914c649badb
Revises: 20b10789ba16
Create Date: 2026-10-06 09:47:20.765695

"""

from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7914c649badb"
down_revision: Union[str, Sequence[str], None] = "20b10789ba16"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


POLICY_VERSION = "POL-2026.09"
POLICY_VERSION_ID = "POLICY-VERSION-2026.09"
RULE_CODE = "KYC_BANK_VALIDATION"
RULE_ID = "KYC_BANK_VALIDATION-2026.09"
EFFECTIVE_FROM = datetime(2026, 9, 1)


def upgrade() -> None:
    """Ensure the governed policy version and KYC rule exist."""
    bind = op.get_bind()

    # ---------------------------------------------------------
    # 1. Ensure policy version exists
    # ---------------------------------------------------------
    policy = bind.execute(
        sa.text(
            """
            SELECT policy_version_id
            FROM policy_versions
            WHERE policy_version = :policy_version
            """
        ),
        {
            "policy_version": POLICY_VERSION,
        },
    ).fetchall()

    if len(policy) > 1:
        raise RuntimeError("DUPLICATE_POLICY_VERSION")

    if len(policy) == 0:
        bind.execute(
            sa.text(
                """
                INSERT INTO policy_versions (
                    policy_version_id,
                    policy_version,
                    effective_from,
                    effective_to,
                    status,
                    policy_reference,
                    governance_notes,
                    created_at,
                    updated_at
                )
                VALUES (
                    :policy_version_id,
                    :policy_version,
                    :effective_from,
                    NULL,
                    'ACTIVE',
                    :policy_reference,
                    :governance_notes,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "policy_version_id": POLICY_VERSION_ID,
                "policy_version": POLICY_VERSION,
                "effective_from": EFFECTIVE_FROM,
                "policy_reference": "GOVERNED_CREDIT_POLICY",
                "governance_notes": (
                    "Active governed policy version used for credit underwriting."
                ),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
        )

    # ---------------------------------------------------------
    # 2. Ensure KYC policy rule exists
    # ---------------------------------------------------------
    existing = bind.execute(
        sa.text(
            """
            SELECT rule_id
            FROM credit_policy_rules
            WHERE policy_version = :policy_version
              AND rule_code = :rule_code
            """
        ),
        {
            "policy_version": POLICY_VERSION,
            "rule_code": RULE_CODE,
        },
    ).fetchall()

    if len(existing) > 1:
        raise RuntimeError("DUPLICATE_KYC_POLICY_RULE")

    rule_parameters = (
        "{"
        '"pan_required": true,'
        '"ekyc_required": true,'
        '"required_ekyc_result": "VERIFIED",'
        '"aadhaar_kyc_required": false,'
        '"policy_source": "COMPANY_FIXED_POLICY"'
        "}"
    )

    if len(existing) == 1:
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
                "rule_parameters": rule_parameters,
                "policy_version": POLICY_VERSION,
                "rule_code": RULE_CODE,
            },
        )
        return

    # Prevent a primary-key collision if the rule ID is already
    # being used by another policy rule.
    rule_id_exists = bind.execute(
        sa.text(
            """
            SELECT 1
            FROM credit_policy_rules
            WHERE rule_id = :rule_id
            """
        ),
        {
            "rule_id": RULE_ID,
        },
    ).first()

    if rule_id_exists is not None:
        raise RuntimeError("RULE_ID_ALREADY_IN_USE")

    bind.execute(
        sa.text(
            """
            INSERT INTO credit_policy_rules (
                rule_id,
                rule_code,
                rule_name,
                rule_description,
                rule_type,
                threshold_value,
                threshold_text,
                action,
                rule_parameters,
                is_active,
                policy_version,
                effective_from,
                effective_to,
                created_at
            )
            VALUES (
                :rule_id,
                :rule_code,
                :rule_name,
                :rule_description,
                :rule_type,
                NULL,
                NULL,
                :action,
                CAST(:rule_parameters AS JSONB),
                TRUE,
                :policy_version,
                :effective_from,
                NULL,
                :created_at
            )
            """
        ),
        {
            "rule_id": RULE_ID,
            "rule_code": RULE_CODE,
            "rule_name": "KYC and Bank Account Validation",
            "rule_description": (
                "Validates required KYC and eKYC conditions "
                "for credit policy evaluation."
            ),
            "rule_type": "VALIDATION",
            "action": "REFER",
            "rule_parameters": rule_parameters,
            "policy_version": POLICY_VERSION,
            "effective_from": EFFECTIVE_FROM,
            "created_at": datetime.utcnow(),
        },
    )


def downgrade() -> None:
    """Remove the fixed KYC policy rule parameters."""
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
            "policy_version": POLICY_VERSION,
            "rule_code": RULE_CODE,
        },
    )