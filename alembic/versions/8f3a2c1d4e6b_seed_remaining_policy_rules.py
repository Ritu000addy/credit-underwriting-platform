"""seed remaining governed policy rules

Revision ID: 8f3a2c1d4e6b
Revises: 7914c649badb
Create Date: 2026-10-07
"""

import json
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8f3a2c1d4e6b"
down_revision: Union[str, Sequence[str], None] = "7914c649badb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


POLICY_VERSION = "POL-2026.09"
EFFECTIVE_FROM = datetime(2026, 9, 1)


POLICY_RULES = [
    {
        "rule_code": "AGE",
        "rule_name": "Age Eligibility",
        "rule_description": (
            "Validates borrower age against the governed minimum "
            "and maximum age limits."
        ),
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
        "rule_description": (
            "Validates borrower income against the governed "
            "minimum income requirement."
        ),
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
        "rule_description": (
            "Validates borrower geography against governed "
            "serviceable geography criteria."
        ),
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
        "rule_description": (
            "Validates credit bureau score against the governed "
            "minimum score."
        ),
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
        "rule_description": (
            "Validates borrower exposure against the governed "
            "maximum exposure limit."
        ),
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
        "rule_description": (
            "Validates borrower repayment obligation against "
            "the governed maximum FOIR limit."
        ),
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
        "rule_description": (
            "Validates employment or business vintage and "
            "repayment history against governed criteria."
        ),
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
        "rule_description": (
            "Validates requested loan amount and tenure against "
            "governed product limits."
        ),
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
        "rule_description": (
            "Controls whether governed policy exceptions are "
            "enabled and which exception rules apply."
        ),
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
    """Ensure all governed underwriting policy rules exist."""

    bind = op.get_bind()

    # ---------------------------------------------------------
    # 1. Verify the governed policy version exists
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

    if len(policy) != 1:
        raise RuntimeError("POLICY_VERSION_NOT_FOUND")
