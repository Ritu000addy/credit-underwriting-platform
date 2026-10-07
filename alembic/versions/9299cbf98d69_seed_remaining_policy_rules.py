"""seed remaining policy rules

Revision ID: 9299cbf98d69
Revises: 8f3a2c1d4e6b
"""

import json
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9299cbf98d69"
down_revision: Union[str, Sequence[str], None] = "8f3a2c1d4e6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


POLICY_VERSION = "POL-2026.09"
EFFECTIVE_FROM = datetime(2026, 9, 1)


POLICY_RULES = [
    {
        "rule_code": "AGE",
        "rule_name": "Age Eligibility",
        "rule_description": "Validates borrower age against governed minimum and maximum age limits.",
        "rule_type": "ELIGIBILITY",
        "action": "REFER",
        "rule_parameters": {
            "min_age": 21,
            "max_age": 60,
            "policy_source": "COMPANY_FIXED_POLICY",
        },
    },
    {
        "rule_code": "INCOME_ELIGIBILITY",
        "rule_name": "Income Eligibility",
        "rule_description": "Validates borrower income against the governed minimum income requirement.",
        "rule_type": "ELIGIBILITY",
        "action": "REFER",
        "rule_parameters": {
            "minimum_income": 25000,
            "policy_source": "COMPANY_FIXED_POLICY",
        },
    },
    {
        "rule_code": "GEOGRAPHY",
        "rule_name": "Geography Eligibility",
        "rule_description": "Validates borrower geography against governed serviceable geography criteria.",
        "rule_type": "ELIGIBILITY",
        "action": "REFER",
        "rule_parameters": {
            "serviceable_states": [],
            "serviceable_cities": [],
            "serviceable_pincodes": [],
            "policy_source": "COMPANY_FIXED_POLICY",
        },
    },
    {
        "rule_code": "BUREAU",
        "rule_name": "Credit Bureau Eligibility",
        "rule_description": "Validates credit bureau score against the governed minimum score.",
        "rule_type": "ELIGIBILITY",
        "action": "REFER",
        "rule_parameters": {
            "minimum_score": 650,
            "policy_source": "COMPANY_FIXED_POLICY",
        },
    },
    {
        "rule_code": "EXPOSURE",
        "rule_name": "Maximum Credit Exposure",
        "rule_description": "Validates borrower exposure against the governed maximum exposure limit.",
        "rule_type": "LIMIT",
        "action": "REFER",
        "rule_parameters": {
            "maximum_exposure": 500000,
            "policy_source": "COMPANY_FIXED_POLICY",
        },
    },
    {
        "rule_code": "FOIR_DTI",
        "rule_name": "FOIR and DTI Validation",
        "rule_description": "Validates borrower repayment obligation against the governed maximum FOIR limit.",
        "rule_type": "LIMIT",
        "action": "REFER",
        "rule_parameters": {
            "maximum_foir": 50,
            "policy_source": "COMPANY_FIXED_POLICY",
        },
    },
    {
        "rule_code": "VINTAGE_REPAYMENT",
        "rule_name": "Vintage and Repayment Validation",
        "rule_description": "Validates employment or business vintage and repayment history against governed criteria.",
        "rule_type": "VALIDATION",
        "action": "REFER",
        "rule_parameters": {
            "minimum_vintage": None,
            "policy_source": "COMPANY_FIXED_POLICY",
        },
    },
    {
        "rule_code": "LOAN_AMOUNT_TENURE",
        "rule_name": "Loan Amount and Tenure Eligibility",
        "rule_description": "Validates requested loan amount and tenure against governed product limits.",
        "rule_type": "ELIGIBILITY",
        "action": "REFER",
        "rule_parameters": {
            "minimum_amount": 50000,
            "maximum_amount": 500000,
            "minimum_tenure_months": 6,
            "maximum_tenure_months": 60,
            "policy_source": "COMPANY_FIXED_POLICY",
        },
    },
    {
        "rule_code": "POLICY_EXCEPTION",
        "rule_name": "Policy Exception",
        "rule_description": "Controls whether governed policy exceptions are enabled and which exception rules apply.",
        "rule_type": "CONTROL",
        "action": "REFER",
        "rule_parameters": {
            "enabled": False,
            "rules": [],
            "policy_source": "COMPANY_FIXED_POLICY",
        },
    },
]


def upgrade() -> None:
    bind = op.get_bind()

    policy = bind.execute(
        sa.text(
            """
            SELECT policy_version_id
            FROM policy_versions
            WHERE policy_version = :policy_version
            """
        ),
        {"policy_version": POLICY_VERSION},
    ).fetchall()

    if len(policy) != 1:
        raise RuntimeError("POLICY_VERSION_NOT_FOUND")

    for rule in POLICY_RULES:
        rule_code = rule["rule_code"]
        rule_id = f"{rule_code}-2026.09"
        parameters_json = json.dumps(rule["rule_parameters"])

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
                "rule_code": rule_code,
            },
        ).fetchall()

        if len(existing) > 1:
            raise RuntimeError(
                f"DUPLICATE_POLICY_RULE:{rule_code}"
            )

        if len(existing) == 1:
            bind.execute(
                sa.text(
                    """
                    UPDATE credit_policy_rules
                    SET rule_name = :rule_name,
                        rule_description = :rule_description,
                        rule_type = :rule_type,
                        action = :action,
                        rule_parameters = CAST(:rule_parameters AS JSONB),
                        is_active = TRUE,
                        effective_from = :effective_from,
                        effective_to = NULL
                    WHERE policy_version = :policy_version
                      AND rule_code = :rule_code
                    """
                ),
                {
                    "policy_version": POLICY_VERSION,
                    "rule_code": rule_code,
                    "rule_name": rule["rule_name"],
                    "rule_description": rule["rule_description"],
                    "rule_type": rule["rule_type"],
                    "action": rule["action"],
                    "rule_parameters": parameters_json,
                    "effective_from": EFFECTIVE_FROM,
                },
            )
            continue

        rule_id_exists = bind.execute(
            sa.text(
                """
                SELECT 1
                FROM credit_policy_rules
                WHERE rule_id = :rule_id
                """
            ),
            {"rule_id": rule_id},
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
                "rule_id": rule_id,
                "rule_code": rule_code,
                "rule_name": rule["rule_name"],
                "rule_description": rule["rule_description"],
                "rule_type": rule["rule_type"],
                "action": rule["action"],
                "rule_parameters": parameters_json,
                "policy_version": POLICY_VERSION,
                "effective_from": EFFECTIVE_FROM,
                "created_at": datetime.utcnow(),
            },
        )


def downgrade() -> None:
    bind = op.get_bind()

    for rule in POLICY_RULES:
        bind.execute(
            sa.text(
                """
                DELETE FROM credit_policy_rules
                WHERE policy_version = :policy_version
                  AND rule_code = :rule_code
                """
            ),
            {
                "policy_version": POLICY_VERSION,
                "rule_code": rule["rule_code"],
            },
        )