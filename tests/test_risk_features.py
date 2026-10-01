from backend.app.schemas.risk_features import CreditRiskFeatures

features = CreditRiskFeatures(
    bureau_score=742,
    dpd=0,
    credit_enquiries=2,
    active_loans=2,
    write_offs=0.0,
    past_loan_count=2,
    repayment_history_count=2,
    internal_dpd_count=0,
    collection_count=0,
    monthly_credits=80000,
    monthly_debits=45000,
    bank_balance=120000,
    existing_emi=15000,
    bounce_count=0,
    monthly_salary=80000,
    employer="Synthetic Employer",
    income_trend="STABLE",
)

print(features.model_dump())