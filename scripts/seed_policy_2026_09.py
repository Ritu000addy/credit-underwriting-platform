from datetime import datetime
from decimal import Decimal

from backend.app.database import SessionLocal
from backend.app.models.policy_version import PolicyVersion
from backend.app.models.credit_policy_rule import CreditPolicyRule


POLICY_VERSION = "POL-2026.09"

EFFECTIVE_FROM = datetime(
    2026,
    9,
    1,
)

RULES = [
    {
        "rule_code": "AGE",
        "rule_name": "Age Eligibility",
        "rule_description": "Applicant age must be within permitted range.",
        "rule_type": "RANGE",
        "threshold_value": None,
        "threshold_text": None,
        "action": "REJECT",
        "rule_parameters": {
            "min_age": 21,
            "max_age": 60,
        },
    },
    {
        "rule_code": "INCOME_ELIGIBILITY",
        "rule_name": "Minimum Income Eligibility",
        "rule_description": "Applicant monthly income must meet minimum requirement.",
        "rule_type": "MINIMUM",
        "threshold_value": Decimal("25000"),
        "threshold_text": None,
        "action": "REJECT",
        "rule_parameters": {
            "minimum_income": 25000,
        },
    },
    {
        "rule_code": "GEOGRAPHY",
        "rule_name": "Serviceable Geography",
        "rule_description": "Applicant must fall within serviceable geography.",
        "rule_type": "LIST",
        "threshold_value": None,
        "threshold_text": None,
        "action": "REJECT",
        "rule_parameters": {
            "serviceable_states": [],
            "serviceable_cities": [],
            "serviceable_pincodes": [],
        },
    },
    {
        "rule_code": "BUREAU",
        "rule_name": "Minimum Bureau Score",
        "rule_description": "Applicant bureau score must meet minimum threshold.",
        "rule_type": "MINIMUM",
        "threshold_value": Decimal("650"),
        "threshold_text": None,
        "action": "REJECT",
        "rule_parameters": {
            "minimum_score": 650,
        },
    },
    {
        "rule_code": "EXPOSURE",
        "rule_name": "Maximum Existing Exposure",
        "rule_description": "Existing outstanding exposure must remain within permitted limit.",
        "rule_type": "MAXIMUM",
        "threshold_value": Decimal("500000"),
        "threshold_text": None,
        "action": "REJECT",
        "rule_parameters": {
            "maximum_exposure": 500000,
        },
    },
    {
        "rule_code": "FOIR_DTI",
        "rule_name": "Maximum FOIR",
        "rule_description": "FOIR must remain within permitted limit.",
        "rule_type": "MAXIMUM",
        "threshold_value": Decimal("50"),
        "threshold_text": None,
        "action": "REJECT",
        "rule_parameters": {
            "maximum_foir": 50,
        },
    },
    {
        "rule_code": "VINTAGE_REPAYMENT",
        "rule_name": "Vintage and Repayment Behaviour",
        "rule_description": "Applicant repayment behaviour must satisfy policy requirements.",
        "rule_type": "REPAYMENT",
        "threshold_value": None,
        "threshold_text": None,
        "action": "REJECT",
        "rule_parameters": {
            "minimum_vintage": None,
        },
    },
    {
        "rule_code": "KYC_BANK_VALIDATION",
        "rule_name": "KYC and Bank Validation",
        "rule_description": "KYC requirements must be satisfied.",
        "rule_type": "VALIDATION",
        "threshold_value": None,
        "threshold_text": None,
        "action": "REJECT",
        "rule_parameters": {},
    },
    {
        "rule_code": "LOAN_AMOUNT_TENURE",
        "rule_name": "Loan Amount and Tenure",
        "rule_description": "Requested amount and tenure must be within permitted limits.",
        "rule_type": "RANGE",
        "threshold_value": None,
        "threshold_text": None,
        "action": "REJECT",
        "rule_parameters": {
            "minimum_amount": 50000,
            "maximum_amount": 500000,
            "minimum_tenure_months": 6,
            "maximum_tenure_months": 60,
        },
    },
    {
        "rule_code": "POLICY_EXCEPTION",
        "rule_name": "Policy Exception",
        "rule_description": "Controlled policy exceptions.",
        "rule_type": "EXCEPTION",
        "threshold_value": None,
        "threshold_text": None,
        "action": "REFER",
        "rule_parameters": {
            "enabled": False,
            "rules": [],
        },
    },
]


def seed_policy():
    db = SessionLocal()

    try:
        policy = (
            db.query(PolicyVersion)
            .filter(
                PolicyVersion.policy_version == POLICY_VERSION
            )
            .first()
        )

        if policy is None:
            policy = PolicyVersion(
                policy_version_id="POLVER-2026.09",
                policy_version=POLICY_VERSION,
                effective_from=EFFECTIVE_FROM,
                effective_to=None,
                status="ACTIVE",
                policy_reference="POLICY_CONFIG_2026.09",
                governance_notes=(
                    "Initial governed policy version migrated "
                    "from POLICY_CONFIG."
                ),
            )

            db.add(policy)
            db.flush()

        else:
            policy.effective_from = EFFECTIVE_FROM
            policy.effective_to = None
            policy.status = "ACTIVE"

        existing_rules = {
            rule.rule_code: rule
            for rule in (
                db.query(CreditPolicyRule)
                .filter(
                    CreditPolicyRule.policy_version
                    == POLICY_VERSION
                )
                .all()
            )
        }

        for item in RULES:
            rule = existing_rules.get(
                item["rule_code"]
            )

            if rule is None:
                rule = CreditPolicyRule(
                    rule_id=(
                        f"PR-{POLICY_VERSION.replace('.', '-')}-"
                        f"{item['rule_code']}"
                    ),
                    rule_code=item["rule_code"],
                    rule_name=item["rule_name"],
                    rule_description=item["rule_description"],
                    rule_type=item["rule_type"],
                    threshold_value=item["threshold_value"],
                    threshold_text=item["threshold_text"],
                    action=item["action"],
                    is_active=True,
                    policy_version=POLICY_VERSION,
                    effective_from=EFFECTIVE_FROM,
                    effective_to=None,
                    rule_parameters=item["rule_parameters"],
                )

                db.add(rule)

            else:
                rule.rule_name = item["rule_name"]
                rule.rule_description = item["rule_description"]
                rule.rule_type = item["rule_type"]
                rule.threshold_value = item["threshold_value"]
                rule.threshold_text = item["threshold_text"]
                rule.action = item["action"]
                rule.is_active = True
                rule.effective_from = EFFECTIVE_FROM
                rule.effective_to = None
                rule.rule_parameters = item["rule_parameters"]

        db.commit()

        print(
            f"POLICY SEEDED: {POLICY_VERSION}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_policy()