from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.models.credit_policy_rule import CreditPolicyRule


class CreditPolicyRuleService:

    def create_rule(
        self,
        db: Session,
        rule_id: str,
        rule_code: str,
        rule_name: str,
        policy_version: str,
        rule_description: str | None = None,
        rule_type: str | None = None,
        threshold_value=None,
        threshold_text: str | None = None,
        action: str | None = None,
        is_active: bool = True,
        effective_from: datetime | None = None,
        effective_to: datetime | None = None,
    ) -> CreditPolicyRule:

        rule = CreditPolicyRule(
            rule_id=rule_id,
            rule_code=rule_code,
            rule_name=rule_name,
            rule_description=rule_description,
            rule_type=rule_type,
            threshold_value=threshold_value,
            threshold_text=threshold_text,
            action=action,
            is_active=is_active,
            policy_version=policy_version,
            effective_from=effective_from,
            effective_to=effective_to,
        )

        db.add(rule)
        db.commit()
        db.refresh(rule)

        return rule


credit_policy_rule_service = CreditPolicyRuleService()