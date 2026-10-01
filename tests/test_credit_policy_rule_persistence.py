from decimal import Decimal

from backend.app.database import SessionLocal
from backend.app.services.credit_policy_rule_service import (
    credit_policy_rule_service,
)


db = SessionLocal()

try:
    result = credit_policy_rule_service.create_rule(
        db=db,
        rule_id="DEV-RULE-001",
        rule_code="DEV_TEST_RULE",
        rule_name="Development Test Rule",
        rule_description="Persistence test rule. Not a production credit policy.",
        rule_type="TEST",
        threshold_value=Decimal("0"),
        threshold_text=None,
        action="REFER",
        is_active=True,
        policy_version="POL-DEV-TEST-01",
    )

    print("POLICY RULE SAVED")
    print("rule_id:", result.rule_id)
    print("rule_code:", result.rule_code)
    print("rule_name:", result.rule_name)
    print("rule_type:", result.rule_type)
    print("threshold_value:", result.threshold_value)
    print("action:", result.action)
    print("is_active:", result.is_active)
    print("policy_version:", result.policy_version)

finally:
    db.close()