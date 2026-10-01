from backend.app.schemas.underwriting import UnderwritingResult

result = UnderwritingResult(
    application_id="APP001",
    customer_id="CUS001",
)

print(result.model_dump())