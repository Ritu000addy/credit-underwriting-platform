import os

from dataclasses import dataclass


@dataclass
class BankRoutingResult:
    success: bool
    provider: str
    routing_reference: str | None = None
    failure_reason: str | None = None


class BankRoutingService:
    """
    Development routing simulator.

    This class does not perform real bank transfers. A live provider
    integration must implement authenticated provider calls and use the
    stable disbursement_id as the provider's idempotency reference.
    """

    SIMULATED_PROVIDERS = frozenset(
        {
            "DEV-BANK-PROVIDER",
            "DEV-BANK-TIMEOUT-ONCE",
            "DEV-PAYMENT-PROVIDER",
        }
    )

    ALLOWED_SIMULATION_ENVIRONMENTS = frozenset(
        {"development", "test"}
    )

    def __init__(self):
        # Development-only transient failure simulation.
        self._timeout_attempts: set[str] = set()

    def route_disbursement(
        self,
        payment_provider: str | None,
        disbursement_id: str,
    ) -> BankRoutingResult:
        provider = (
            payment_provider.strip().upper()
            if isinstance(payment_provider, str)
            else ""
        )
        
        if not provider:
            return BankRoutingResult(
                success=False,
                provider="UNKNOWN",
                failure_reason="PAYMENT_PROVIDER_NOT_CONFIGURED",
            )

        app_env = os.getenv("APP_ENV", "").strip().lower()
        routing_mode = (
            os.getenv("BANK_ROUTING_MODE", "DISABLED")
            .strip()
            .upper()
        )

        # Never simulate a successful transfer in production or when
        # development simulation has not been explicitly enabled.
        if (
            app_env not in self.ALLOWED_SIMULATION_ENVIRONMENTS
            or routing_mode != "SIMULATED"
        ):
            return BankRoutingResult(
                success=False,
                provider=provider,
                failure_reason="BANK_ROUTING_NOT_CONFIGURED",
            )

        # Only explicitly declared development providers are simulated.
        if provider not in self.SIMULATED_PROVIDERS:
            return BankRoutingResult(
                success=False,
                provider=provider,
                failure_reason="PAYMENT_PROVIDER_NOT_CONFIGURED",
            )

        # Deterministic timeout simulation for retry testing.
        if provider == "DEV-BANK-TIMEOUT-ONCE":
            if disbursement_id not in self._timeout_attempts:
                self._timeout_attempts.add(disbursement_id)

                return BankRoutingResult(
                    success=False,
                    provider=provider,
                    failure_reason="BANK_TIMEOUT",
                )

        # This is a synthetic reference, not a bank transaction reference.
        # It remains deterministic for a given disbursement across retries.
        return BankRoutingResult(
            success=True,
            provider=provider,
            routing_reference=f"SIM-ROUTE-{disbursement_id}",
        )

bank_routing_service = BankRoutingService()