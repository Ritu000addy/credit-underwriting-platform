from dataclasses import dataclass


@dataclass
class BankRoutingResult:
    success: bool
    provider: str
    routing_reference: str | None = None
    failure_reason: str | None = None


class BankRoutingService:

    def __init__(self):
        # Development-only state used to simulate a transient
        # bank failure for retry testing.
        self._timeout_attempts: set[str] = set()

    def route_disbursement(
        self,
        payment_provider: str | None,
        disbursement_id: str,
    ) -> BankRoutingResult:

        if not payment_provider:
            return BankRoutingResult(
                success=False,
                provider="UNKNOWN",
                failure_reason="PAYMENT_PROVIDER_NOT_CONFIGURED",
            )

        # Development-only transient failure simulation.
        # First attempt fails; subsequent attempt succeeds.
        if payment_provider == "DEV-BANK-TIMEOUT-ONCE":
            if disbursement_id not in self._timeout_attempts:
                self._timeout_attempts.add(disbursement_id)

                return BankRoutingResult(
                    success=False,
                    provider=payment_provider,
                    failure_reason="BANK_TIMEOUT",
                )

        # Development routing only.
        # Real bank/provider API integration will be added later.
        routing_reference = f"ROUTE-{disbursement_id}"

        return BankRoutingResult(
            success=True,
            provider=payment_provider,
            routing_reference=routing_reference,
        )


bank_routing_service = BankRoutingService()