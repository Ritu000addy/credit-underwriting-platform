
from backend.app.services.bank_routing_service import BankRoutingService


def enable_simulation(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("BANK_ROUTING_MODE", "SIMULATED")


def test_unknown_provider_fails_closed(monkeypatch):
    enable_simulation(monkeypatch)
    service = BankRoutingService()

    result = service.route_disbursement(
        payment_provider="REAL-BANK-NAME",
        disbursement_id="DISB-ROUTING-001",
    )

    assert result.success is False
    assert result.failure_reason == "PAYMENT_PROVIDER_NOT_CONFIGURED"
    assert result.routing_reference is None


def test_simulation_is_disabled_without_explicit_mode(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("BANK_ROUTING_MODE", raising=False)
    service = BankRoutingService()

    result = service.route_disbursement(
        payment_provider="DEV-BANK-PROVIDER",
        disbursement_id="DISB-ROUTING-002",
    )

    assert result.success is False
    assert result.failure_reason == "BANK_ROUTING_NOT_CONFIGURED"


def test_simulation_is_disabled_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("BANK_ROUTING_MODE", "SIMULATED")
    service = BankRoutingService()

    result = service.route_disbursement(
        payment_provider="DEV-BANK-PROVIDER",
        disbursement_id="DISB-ROUTING-003",
    )

    assert result.success is False
    assert result.failure_reason == "BANK_ROUTING_NOT_CONFIGURED"


def test_explicit_development_provider_returns_stable_simulated_reference(
    monkeypatch,
):
    enable_simulation(monkeypatch)
    service = BankRoutingService()

    first = service.route_disbursement(
        payment_provider="DEV-BANK-PROVIDER",
        disbursement_id="DISB-ROUTING-004",
    )
    second = service.route_disbursement(
        payment_provider="DEV-BANK-PROVIDER",
        disbursement_id="DISB-ROUTING-004",
    )

    assert first.success is True
    assert first.routing_reference == "SIM-ROUTE-DISB-ROUTING-004"
    assert second.routing_reference == first.routing_reference


def test_timeout_once_simulation_fails_then_succeeds(monkeypatch):
    enable_simulation(monkeypatch)
    service = BankRoutingService()

    first = service.route_disbursement(
        payment_provider="DEV-BANK-TIMEOUT-ONCE",
        disbursement_id="DISB-ROUTING-005",
    )
    second = service.route_disbursement(
        payment_provider="DEV-BANK-TIMEOUT-ONCE",
        disbursement_id="DISB-ROUTING-005",
    )

    assert first.success is False
    assert first.failure_reason == "BANK_TIMEOUT"
    assert second.success is True
    assert second.routing_reference == "SIM-ROUTE-DISB-ROUTING-005"


def test_missing_provider_fails_closed(monkeypatch):
    enable_simulation(monkeypatch)
    service = BankRoutingService()

    result = service.route_disbursement(
        payment_provider=None,
        disbursement_id="DISB-ROUTING-006",
    )

    assert result.success is False
    assert result.failure_reason == "PAYMENT_PROVIDER_NOT_CONFIGURED"
