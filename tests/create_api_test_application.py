from urllib.request import Request, urlopen
import json


payload = {
    "application_id": "API-TEST-001",
    "customer_id": "API-CUST-001",
    "loan_amount": 150000,
    "loan_tenure_months": 12,
    "annual_interest_rate": 12,
}

request = Request(
    "http://127.0.0.1:8000/applications",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)

response = urlopen(request)

print("STATUS:", response.status)
print(json.dumps(
    json.loads(response.read()),
    indent=2,
))