from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.models.credit_policy_rule import CreditPolicyRule
from backend.app.models.policy_version import PolicyVersion


class PolicyVersionService:

    def get_applicable_policy(
        self,
        db: Session,
        as_of: datetime | None = None,
    ) -> PolicyVersion | None:

        if as_of is None:
            as_of = datetime.utcnow()

        return (
            db.query(PolicyVersion)
            .filter(
                PolicyVersion.status == "ACTIVE",
                PolicyVersion.effective_from <= as_of,
                (
                    (PolicyVersion.effective_to.is_(None))
                    | (PolicyVersion.effective_to >= as_of)
                ),
            )
            .order_by(
                PolicyVersion.effective_from.desc()
            )
            .first()
        )

    def get_policy_rules(
        self,
        db: Session,
        policy_version: str,
        as_of: datetime | None = None,
    ) -> list[CreditPolicyRule]:

        if as_of is None:
            as_of = datetime.utcnow()

        return (
            db.query(CreditPolicyRule)
            .filter(
                CreditPolicyRule.policy_version == policy_version,
                CreditPolicyRule.is_active.is_(True),
                CreditPolicyRule.effective_from <= as_of,
                (
                    (CreditPolicyRule.effective_to.is_(None))
                    | (CreditPolicyRule.effective_to >= as_of)
                ),
            )
            .order_by(
                CreditPolicyRule.rule_code.asc()
            )
            .all()
        )

    def get_policy_context(
        self,
        db: Session,
        as_of: datetime | None = None,
    ) -> dict:

        if as_of is None:
            as_of = datetime.utcnow()

        policy = self.get_applicable_policy(
            db=db,
            as_of=as_of,
        )

        if policy is None:
            raise ValueError(
                "ACTIVE_POLICY_NOT_FOUND"
            )

        rules = self.get_policy_rules(
            db=db,
            policy_version=policy.policy_version,
            as_of=as_of,
        )

        if not rules:
            raise ValueError(
                "POLICY_RULES_NOT_CONFIGURED"
            )

        rule_map: dict[str, dict] = {}

        for rule in rules:
            if rule.rule_code in rule_map:
                raise ValueError(
                    f"DUPLICATE_POLICY_RULE:{rule.rule_code}"
                )

            rule_map[rule.rule_code] = (
                rule.rule_parameters or {}
            )

        required_rule_codes = {
            "AGE",
            "INCOME_ELIGIBILITY",
            "GEOGRAPHY",
            "BUREAU",
            "EXPOSURE",
            "FOIR_DTI",
            "VINTAGE_REPAYMENT",
            "KYC_BANK_VALIDATION",
            "LOAN_AMOUNT_TENURE",
            "POLICY_EXCEPTION",
        }

        missing_rules = (
            required_rule_codes
            - set(rule_map.keys())
        )

        if missing_rules:
            raise ValueError(
                "POLICY_RULE_CONFIGURATION_INCOMPLETE:"
                + ",".join(sorted(missing_rules))
            )

        policy_config = {
            "age": {
                "min_age": rule_map["AGE"].get("min_age"),
                "max_age": rule_map["AGE"].get("max_age"),
            },

            "income": {
                "minimum_income": rule_map[
                    "INCOME_ELIGIBILITY"
                ].get("minimum_income"),
            },

            "geography": {
                "serviceable_states": rule_map[
                    "GEOGRAPHY"
                ].get("serviceable_states", []),
                "serviceable_cities": rule_map[
                    "GEOGRAPHY"
                ].get("serviceable_cities", []),
                "serviceable_pincodes": rule_map[
                    "GEOGRAPHY"
                ].get("serviceable_pincodes", []),
            },

            "bureau": {
                "minimum_score": rule_map[
                    "BUREAU"
                ].get("minimum_score"),
            },

            "exposure": {
                "maximum_exposure": rule_map[
                    "EXPOSURE"
                ].get("maximum_exposure"),
            },

            "foir": {
                "maximum_foir": rule_map[
                    "FOIR_DTI"
                ].get("maximum_foir"),
            },

            "vintage": {
                "minimum_vintage": rule_map[
                    "VINTAGE_REPAYMENT"
                ].get("minimum_vintage"),
            },

            "kyc_bank_validation": {
                "pan_required": rule_map[
                    "KYC_BANK_VALIDATION"
                ].get("pan_required", True),

                "ekyc_required": rule_map[
                    "KYC_BANK_VALIDATION"
                ].get("ekyc_required", True),

                "required_ekyc_result": rule_map[
                    "KYC_BANK_VALIDATION"
                ].get("required_ekyc_result", "VERIFIED"),

                "aadhaar_kyc_required": rule_map[
                    "KYC_BANK_VALIDATION"
                ].get("aadhaar_kyc_required", False),
            },

            "exceptions": {
                "enabled": rule_map[
                    "POLICY_EXCEPTION"
                ].get("enabled", False),
                "rules": rule_map[
                    "POLICY_EXCEPTION"
                ].get("rules", []),
            },

            "loan": {
                "minimum_amount": rule_map[
                    "LOAN_AMOUNT_TENURE"
                ].get("minimum_amount"),
                "maximum_amount": rule_map[
                    "LOAN_AMOUNT_TENURE"
                ].get("maximum_amount"),
                "minimum_tenure_months": rule_map[
                    "LOAN_AMOUNT_TENURE"
                ].get("minimum_tenure_months"),
                "maximum_tenure_months": rule_map[
                    "LOAN_AMOUNT_TENURE"
                ].get("maximum_tenure_months"),
            },
        }

        policy_metadata = {
            "policy_version": policy.policy_version,
            "effective_from": policy.effective_from.strftime(
                "%Y-%m-%d"
            ),
            "effective_to": (
                policy.effective_to.strftime("%Y-%m-%d")
                if policy.effective_to is not None
                else None
            ),
            "status": policy.status,
        }

        return {
            "policy_config": policy_config,
            "policy_metadata": policy_metadata,
            "policy_version_record": policy,
            "policy_rules": rules,
            "as_of": as_of,
        }

    def get_policy_version(
        self,
        db: Session,
        policy_version: str,
    ) -> PolicyVersion:

        policy = (
            db.query(PolicyVersion)
            .filter(
                PolicyVersion.policy_version == policy_version
            )
            .first()
        )

        if policy is None:
            raise ValueError(
                f"POLICY_VERSION_NOT_FOUND:{policy_version}"
            )

        return policy

    def create_policy_version(
        self,
        db: Session,
        policy_version: str,
        effective_from: datetime,
        effective_to: datetime | None = None,
        policy_reference: str | None = None,
        governance_notes: str | None = None,
    ) -> PolicyVersion:

        existing = (
            db.query(PolicyVersion)
            .filter(
                PolicyVersion.policy_version == policy_version
            )
            .first()
        )

        if existing is not None:
            raise ValueError(
                f"DUPLICATE_POLICY_VERSION:{policy_version}"
            )

        if (
            effective_to is not None
            and effective_to < effective_from
        ):
            raise ValueError(
                "POLICY_EFFECTIVE_TO_BEFORE_EFFECTIVE_FROM"
            )

        policy = PolicyVersion(
            policy_version_id=f"POLICY-VERSION-{policy_version.split('POL-')[-1]}",
            policy_version=policy_version,
            effective_from=effective_from,
            effective_to=effective_to,
            status="DRAFT",
            policy_reference=policy_reference,
            governance_notes=governance_notes,
        )

        db.add(policy)
        db.flush()

        return policy

    def activate_policy(
        self,
        db: Session,
        policy_version: str,
        as_of: datetime | None = None,
    ) -> PolicyVersion:

        if as_of is None:
            as_of = datetime.utcnow()

        policy = self.get_policy_version(
            db=db,
            policy_version=policy_version,
        )

        if policy.status == "ACTIVE":
            return policy

        if policy.status not in {
            "DRAFT",
            "INACTIVE",
            "ROLLED_BACK",
        }:
            raise ValueError(
                f"POLICY_ACTIVATION_NOT_ALLOWED:{policy.status}"
            )

        if policy.effective_from > as_of:
            raise ValueError(
                "POLICY_EFFECTIVE_FROM_IN_FUTURE"
            )

        if (
            policy.effective_to is not None
            and policy.effective_to < as_of
        ):
            raise ValueError(
                "POLICY_ALREADY_EXPIRED"
            )

        rules = self.get_policy_rules(
            db=db,
            policy_version=policy.policy_version,
            as_of=as_of,
        )

        if not rules:
            raise ValueError(
                "POLICY_RULES_NOT_CONFIGURED"
            )

        current_active = (
            db.query(PolicyVersion)
            .filter(
                PolicyVersion.status == "ACTIVE",
                PolicyVersion.policy_version != policy.policy_version,
            )
            .all()
        )

        for current in current_active:
            current.status = "INACTIVE"

        policy.status = "ACTIVE"

        db.flush()

        return policy

    def deactivate_policy(
        self,
        db: Session,
        policy_version: str,
    ) -> PolicyVersion:

        policy = self.get_policy_version(
            db=db,
            policy_version=policy_version,
        )

        if policy.status != "ACTIVE":
            raise ValueError(
                f"POLICY_DEACTIVATION_NOT_ALLOWED:{policy.status}"
            )

        other_active_exists = (
            db.query(PolicyVersion)
            .filter(
                PolicyVersion.status == "ACTIVE",
                PolicyVersion.policy_version != policy.policy_version,
            )
            .first()
        )

        if other_active_exists is None:
            raise ValueError(
                "CANNOT_DEACTIVATE_ONLY_ACTIVE_POLICY"
            )

        policy.status = "INACTIVE"

        db.flush()

        return policy

    def retire_policy(
        self,
        db: Session,
        policy_version: str,
    ) -> PolicyVersion:

        policy = self.get_policy_version(
            db=db,
            policy_version=policy_version,
        )

        if policy.status not in {
            "INACTIVE",
            "ROLLED_BACK",
        }:
            raise ValueError(
                f"POLICY_RETIRE_NOT_ALLOWED:{policy.status}"
            )

        policy.status = "RETIRED"

        db.flush()

        return policy

    def rollback_policy(
        self,
        db: Session,
        target_policy_version: str,
        as_of: datetime | None = None,
    ) -> PolicyVersion:

        if as_of is None:
            as_of = datetime.utcnow()

        current_active = (
            db.query(PolicyVersion)
            .filter(
                PolicyVersion.status == "ACTIVE"
            )
            .first()
        )

        if current_active is None:
            raise ValueError(
                "ACTIVE_POLICY_NOT_FOUND"
            )

        target = self.get_policy_version(
            db=db,
            policy_version=target_policy_version,
        )

        if (
            target.policy_version
            == current_active.policy_version
        ):
            raise ValueError(
                "POLICY_ROLLBACK_TARGET_IS_CURRENT"
            )

        if target.status not in {
            "INACTIVE",
            "ROLLED_BACK",
        }:
            raise ValueError(
                f"POLICY_ROLLBACK_TARGET_INVALID:{target.status}"
            )

        if target.effective_from > as_of:
            raise ValueError(
                "POLICY_EFFECTIVE_FROM_IN_FUTURE"
            )

        if (
            target.effective_to is not None
            and target.effective_to < as_of
        ):
            raise ValueError(
                "POLICY_ROLLBACK_TARGET_EXPIRED"
            )

        rules = self.get_policy_rules(
            db=db,
            policy_version=target.policy_version,
            as_of=as_of,
        )

        if not rules:
            raise ValueError(
                "POLICY_RULES_NOT_CONFIGURED"
            )

        current_active.status = "ROLLED_BACK"
        target.status = "ACTIVE"

        db.flush()

        return target

    def list_policy_versions(
        self,
        db: Session,
    ) -> list[PolicyVersion]:

        return (
            db.query(PolicyVersion)
            .order_by(
                PolicyVersion.effective_from.desc()
            )
            .all()
        )

policy_version_service = PolicyVersionService()