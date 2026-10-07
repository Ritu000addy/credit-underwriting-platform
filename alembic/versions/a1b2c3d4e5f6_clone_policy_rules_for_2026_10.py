"""clone policy rules for POL-2026.10

Revision ID: a1b2c3d4e5f6
Revises: 9299cbf98d69
"""

from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import json


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "9299cbf98d69"
branch_labels = None
depends_on = None


SOURCE_POLICY_VERSION = "POL-2026.09"
TARGET_POLICY_VERSION = "POL-2026.10"
TARGET_EFFECTIVE_FROM = datetime(2026, 10, 7)


def upgrade() -> None:
    bind = op.get_bind()

    # Ensure target policy version exists.
    target_policy = bind.execute(
        sa.text(
            """
            SELECT policy_version_id
            FROM policy_versions
            WHERE policy_version = :policy_version
            """
        ),
        {
            "policy_version": TARGET_POLICY_VERSION,
        },
    ).fetchall()

    if len(target_policy) != 1:
        raise RuntimeError("TARGET_POLICY_VERSION_NOT_FOUND")

    # Read the governed rules from the existing active policy.
    source_rules = bind.execute(
        sa.text(
            """
            SELECT
                rule_code,
                rule_name,
                rule_description,
                rule_type,
                threshold_value,
                threshold_text,
                action,
                rule_parameters
            FROM credit_policy_rules
            WHERE policy_version = :policy_version
              AND is_active = TRUE
            ORDER BY rule_code
            """
        ),
        {
            "policy_version": SOURCE_POLICY_VERSION,
        },
    ).fetchall()

    if len(source_rules) != 10:
        raise RuntimeError(
            f"SOURCE_POLICY_RULE_COUNT_INVALID:{len(source_rules)}"
        )

    for rule in source_rules:
        rule_id = f"{rule.rule_code}-2026.10"

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
                "policy_version": TARGET_POLICY_VERSION,
                "rule_code": rule.rule_code,
            },
        ).first()

        if existing is not None:
            continue

        rule_id_exists = bind.execute(
            sa.text(
                """
                SELECT 1
                FROM credit_policy_rules
                WHERE rule_id = :rule_id
                """
            ),
            {
                "rule_id": rule_id,
            },
        ).first()

        if rule_id_exists is not None:
            raise RuntimeError(
                f"RULE_ID_ALREADY_IN_USE:{rule_id}"
            )

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
                    :threshold_value,
                    :threshold_text,
                    :action,
                    :rule_parameters,
                    TRUE,
                    :policy_version,
                    :effective_from,
                    NULL,
                    :created_at
                )
                """
            ),
            {
                "rule_id": rule_id,
                "rule_code": rule.rule_code,
                "rule_name": rule.rule_name,
                "rule_description": rule.rule_description,
                "rule_type": rule.rule_type,
                "threshold_value": rule.threshold_value,
                "threshold_text": rule.threshold_text,
                "action": rule.action,
                "rule_parameters": json.dumps(rule.rule_parameters)
                    if rule.rule_parameters is not None
                    else None,
                "policy_version": TARGET_POLICY_VERSION,
                "effective_from": TARGET_EFFECTIVE_FROM,
                "created_at": datetime.utcnow(),
            },
        )


def downgrade() -> None:
    bind = op.get_bind()

    bind.execute(
        sa.text(
            """
            DELETE FROM credit_policy_rules
            WHERE policy_version = :policy_version
            """
        ),
        {
            "policy_version": TARGET_POLICY_VERSION,
        },
    )