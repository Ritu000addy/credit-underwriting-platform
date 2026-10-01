# LMS Integration Contract

## 1. Sanction to LMS

### Direction

Credit Underwriting Platform → LMS

### Operation

Create Loan Account

### Current Development Endpoint

POST /lms/sanctions

### Request

- sanction_id
- application_id
- sanctioned_amount
- sanctioned_tenure
- sanctioned_emi
- interest_rate
- sanction_status
- approval_authority
- sanctioned_at
- expires_at

### Response

- loan_account_id
- application_id
- sanction_id
- loan_status
- created_at

## 2. Integration Status

Current implementation is a development adapter.

The actual external LMS integration is pending:

- LMS base URL
- Authentication mechanism
- Production endpoint
- Exact external request contract
- Exact external response contract
- Error response contract
- Timeout/retry requirements
- Idempotency requirements
- Webhook/callback requirements

These values must be supplied by the company's LMS/API specification before production integration.

## 3. Design Boundary

Credit Underwriting Platform
→ LMS Adapter
→ External LMS

The platform's underwriting decision, risk outputs, fraud outputs, policy checks and model governance remain separate from LMS servicing.

The LMS is responsible for downstream loan servicing functions such as loan account, repayment schedule, interest, charges, collections, DPD and servicing.

## 4. Loan Account to Repayment Schedule

### Direction

Credit Underwriting Platform → LMS

### Operation

Create Repayment Schedule

### Current Development Endpoint

POST /lms/repayment-schedules

### Request

- loan_account_id
- application_id
- sanction_id

### Response

- repayment_schedule_id
- loan_account_id
- application_id
- schedule_status
- created_at

### Integration Status

Currently implemented using the development LMS adapter.

The actual LMS repayment schedule API contract is pending confirmation from the company's LMS/API specification.

## 5. Loan Servicing Installment

### Direction

Credit Underwriting Platform → LMS

### Operation

Create Servicing Installment

### Current Development Endpoint

POST /lms/servicing/installments

### Request

- loan_account_id
- application_id
- repayment_schedule_id
- installment_number
- due_date
- principal_due
- interest_due
- total_due

### Response

- repayment_schedule_id
- loan_account_id
- installment_number
- schedule_status

### Integration Status

Currently implemented using the development LMS adapter.

The actual external LMS servicing contract is pending confirmation from the company's LMS/API specification.

Interest is currently represented through the installment-level interest_due field. No separate charge fields are introduced until the actual LMS contract defines the applicable charge structure.

## 6. Loan Status Synchronization

### Direction

Credit Underwriting Platform → LMS

### Operation

Update Loan Status

### Current Development Endpoint

POST /lms/loan-status

### Request

- loan_account_id
- application_id
- loan_status

### Response

- loan_account_id
- application_id
- loan_status
- updated_at

### Integration Status

Currently implemented using the development LMS adapter.

The actual external LMS loan-status synchronization contract, including the integration direction and webhook/callback mechanism, is pending confirmation from the company's LMS/API specification.