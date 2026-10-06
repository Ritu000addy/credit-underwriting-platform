from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def unique(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10].upper()}"


def assert_success(response, step: str):
    assert response.status_code == 200, (
        f"{step} failed: "
        f"status={response.status_code}, "
        f"body={response.text}"
    )


def test_operations_dashboard_and_application_queue():
    customer_id = unique("OPS-CUST")
    application_id = unique("OPS-APP")

    customer_response = client.post(
        "/customers",
        json={
            "customer_id": customer_id,
            "kyc_status": "VERIFIED",
            "pan": "ABCDE1234F",
            "aadhaar_reference": unique("AADHAAR"),
            "aadhaar_kyc_status": "VERIFIED",
            "dob": "1990-01-15",
            "address": "Pune, Maharashtra",
        },
    )

    assert_success(
        customer_response,
        "Operations test customer creation",
    )

    application_response = client.post(
        "/applications",
        json={
            "application_id": application_id,
            "customer_id": customer_id,
            "requested_amount": 150000,
            "loan_tenure_months": 12,
            "annual_interest_rate": 18,
        },
    )

    assert_success(
        application_response,
        "Operations test application creation",
    )

    dashboard_response = client.get(
        "/operations/dashboard"
    )

    assert_success(
        dashboard_response,
        "Operations dashboard",
    )

    dashboard = dashboard_response.json()

    assert "generated_at" in dashboard
    assert "applications" in dashboard
    assert "underwriting" in dashboard
    assert "manual_review" in dashboard
    assert "exceptions" in dashboard
    assert "disbursements" in dashboard
    assert "collections" in dashboard
    assert "reconciliation" in dashboard
    assert "operations_queue" in dashboard

    assert dashboard["applications"]["total"] >= 1

    application_queue_response = client.get(
        "/operations/applications",
        params={
            "application_id": application_id,
        },
    )

    assert_success(
        application_queue_response,
        "Operations application queue",
    )

    queue = application_queue_response.json()

    assert queue["total"] == 1
    assert len(queue["items"]) == 1
    assert (
        queue["items"][0]["application_id"]
        == application_id
    )
    assert (
        queue["items"][0]["customer_id"]
        == customer_id
    )


def test_operations_application_detail():
    customer_id = unique("OPS-CUST")
    application_id = unique("OPS-APP")

    customer_response = client.post(
        "/customers",
        json={
            "customer_id": customer_id,
            "kyc_status": "VERIFIED",
            "pan": "ABCDE1234F",
            "aadhaar_reference": unique("AADHAAR"),
            "aadhaar_kyc_status": "VERIFIED",
            "dob": "1990-01-15",
            "address": "Pune, Maharashtra",
        },
    )

    assert_success(
        customer_response,
        "Operations detail customer creation",
    )

    application_response = client.post(
        "/applications",
        json={
            "application_id": application_id,
            "customer_id": customer_id,
            "requested_amount": 200000,
            "loan_tenure_months": 18,
            "annual_interest_rate": 18,
        },
    )

    assert_success(
        application_response,
        "Operations detail application creation",
    )

    detail_response = client.get(
        f"/operations/applications/{application_id}"
    )

    assert_success(
        detail_response,
        "Operations application detail",
    )

    detail = detail_response.json()

    assert detail["application_id"] == application_id
    assert detail["customer_id"] == customer_id
    assert detail["requested_amount"] == "200000.00"


def test_operations_read_only_queues():
    endpoints = [
        "/operations/manual-review",
        "/operations/exceptions",
        "/operations/disbursements",
        "/operations/reconciliation",
        "/operations/collections/overdue",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)

        assert_success(
            response,
            f"Operations queue {endpoint}",
        )

        assert isinstance(
            response.json(),
            list,
        )