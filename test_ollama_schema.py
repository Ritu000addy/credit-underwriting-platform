import json
import re

from backend.app.services.genai_provider import genai_provider
from backend.app.schemas.genai_underwriting import GenAIUnderwritingResult

prompt = """
Return ONLY valid JSON.
status: REFER
borrower_summary, financial_summary, credit_narrative, officer_summary: strings
strengths, concerns, missing_information, policy_exceptions: arrays of strings
model_name, model_version: strings
Do not invent facts or make a final credit decision.
"""

raw = genai_provider.generate(prompt)
print("RAW RESPONSE:")
print(raw)

cleaned = re.sub(
    r"^```(?:json)?\s*|\s*```$",
    "",
    raw.strip(),
    flags=re.IGNORECASE,
).strip()

data = json.loads(cleaned)
result = GenAIUnderwritingResult.model_validate(data)

print("\nSCHEMA VALIDATION: PASSED")
print(result.model_dump_json(indent=2))
