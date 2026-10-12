import os

from dotenv import load_dotenv
import requests

load_dotenv()


class GenAIProvider:
    SUPPORTED_PROVIDERS = {"NONE", "MOCK", "OPENAI", "OLLAMA"}

    def __init__(self):
        self.provider = os.getenv(
            "GENAI_PROVIDER",
            "NONE",
        ).upper()

        if self.provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(f"GENAI_PROVIDER_UNSUPPORTED: {self.provider}")

        self.model = os.getenv(
            "GENAI_MODEL",
            "",
        )

        self.api_key = os.getenv(
            "GENAI_API_KEY",
            "",
        )

        self.base_url = os.getenv(
            "GENAI_BASE_URL",
            "",
        )

        self.timeout_seconds = int(
            os.getenv(
                "GENAI_TIMEOUT_SECONDS",
                "60",
            )
        )

    def is_configured(self) -> bool:
        if self.provider == "MOCK":
            return bool(self.model)

        if self.provider == "OLLAMA":
            return bool(self.model and self.base_url)

        return (
            self.provider != "NONE"
            and bool(self.model)
            and bool(self.api_key)
        )

    def generate(
        self,
        prompt: str,
    ) -> str:

        if not prompt.strip():
            raise ValueError(
                "GENAI_PROMPT_EMPTY"
            )

        if self.provider == "MOCK":
            return self._generate_mock(prompt)

        if not self.is_configured():
            raise RuntimeError(
                "GenAI provider is not configured."
            )

        if self.provider == "OPENAI":
            return self._generate_openai(prompt)

        if self.provider == "OLLAMA":
            return self._generate_ollama(prompt)

        raise RuntimeError(
            f"GENAI_PROVIDER_UNSUPPORTED: {self.provider}"
        )

    def _generate_mock(self, prompt: str) -> str:
        """
        Development-only mock provider.

        Returns a deterministic structured response so that the complete
        GenAI underwriting pipeline can be tested without an external LLM.
        """
        if os.getenv("GENAI_MOCK_TEST_CASE") == "INVALID_JSON":
            return '{"borrower_summary": '

        if os.getenv("GENAI_MOCK_TEST_CASE") == "INVALID_SCHEMA":
            return '{"strengths": "not-a-list"}'

        if os.getenv("GENAI_MOCK_TEST_CASE") == "GENERATION_FAILURE":
            raise RuntimeError("MOCK_GENERATION_FAILURE")
    
        return """
{
  "borrower_summary": "Borrower has verified KYC and a bureau score of 742.",
  "financial_summary": "Bank cash flow shows stable income, no reported bounces, and 120 transactions.",
  "credit_narrative": "The application is referred based on the existing underwriting decision.",
  "strengths": [],
  "concerns": [],
  "missing_information": [],
  "policy_exceptions": [],
  "officer_summary": "Application is referred for human credit officer review."
}
""".strip()

    def _generate_openai(
        self,
        prompt: str,
    ) -> str:
        
        url = self.base_url or "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a credit analyst assistant."
                        "You assist human credit officers."
                        "You do not make or change the final credit decision."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.1,
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )

        except requests.Timeout as exc:
            raise RuntimeError(
                "GENAI_PROVIDER_TIMEOUT"
            ) from exc

        except requests.RequestException as exc:
            raise RuntimeError(
                "GENAI_PROVIDER_REQUEST_FAILED"
            ) from exc

        if response.status_code >= 400:
            raise RuntimeError(
                "GENAI_PROVIDER_ERROR"
            )

        data = response.json()

        try:
            return data["choices"][0]["message"]["content"]

        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                "GENAI_PROVIDER_INVALID_RESPONSE"
            ) from exc
        
    def _generate_ollama(self, prompt: str) -> str:
        url = self.base_url or "http://localhost:11434/api/chat"

        payload = {
            "model": self.model,
            "keep_alive": "10m",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a credit analyst copilot. "
                        "Use only supplied evidence. Never invent borrower facts. "
                        "Do not make or change credit decisions. "
                        "Return valid JSON matching the requested field types."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.1, 
                "num_predict": 180,
                "num_ctx": 4096,
            },
        }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            raise RuntimeError("GENAI_PROVIDER_TIMEOUT") from exc
        except requests.RequestException as exc:
            raise RuntimeError("GENAI_PROVIDER_REQUEST_FAILED") from exc

        try:
            data = response.json()
            content = data["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("Empty model response")
            return content
        except (ValueError, KeyError, TypeError) as exc:
            raise RuntimeError(
                "GENAI_PROVIDER_INVALID_RESPONSE"
            ) from exc
genai_provider = GenAIProvider()