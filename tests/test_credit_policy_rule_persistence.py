from decimal import Decimal

from datetime import datetime

from backend.app.models.policy_version import PolicyVersion

from backend.app.database import SessionLocal
from backend.app.services.credit_policy_rule_service import (
    credit_policy_rule_service,
)

def test_credit_policy_rule_persistence():
    db = SessionLocal()

    try:
        test_suffix = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")

        policy_version = (
            db.query(PolicyVersion)
            .filter(
                PolicyVersion.policy_version == "POL-DEV-TEST-01"
            )
            .first()
        )

        if policy_version is None:
            policy_version = PolicyVersion(
                policy_version_id=f"DEV-POL-VERSION-{test_suffix}",
                policy_version="POL-DEV-TEST-01",
                effective_from=datetime(2026, 10, 1),
                effective_to=None,
                status="DRAFT",
                policy_reference="Development test policy",
                governance_notes="Test-only policy version.",
            )

            db.add(policy_version)
            db.commit()

        result = credit_policy_rule_service.create_rule(
            db=db,
            rule_id=f"DEV-RULE-{test_suffix}",
            rule_code=f"DEV_TEST_RULE_{test_suffix}",
            rule_name="Development Test Rule",
            rule_description=(
                "Persistence test rule. Not a production credit policy."
            ),
            rule_type="TEST",
            threshold_value=Decimal("0"),
            threshold_text=None,
            action="REFER",
            is_active=True,
            policy_version="POL-DEV-TEST-01",
        )

        assert result.rule_id.startswith("DEV-RULE-")
        assert result.rule_code.startswith("DEV_TEST_RULE_")
        assert result.policy_version == "POL-DEV-TEST-01"
        assert result.action == "REFER"
        assert result.is_active is True

    finally:
        db.close()