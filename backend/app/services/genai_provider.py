import os

from dotenv import load_dotenv


load_dotenv()


class GenAIProvider:

    def __init__(self):
        self.provider = os.getenv(
            "GENAI_PROVIDER",
            "NONE",
        )

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
        return (
            self.provider != "NONE"
            and bool(self.model)
            and bool(self.api_key)
        )

    def generate(
        self,
        prompt: str,
    ) -> str:

        if not self.is_configured():
            raise RuntimeError(
                "GenAI provider is not configured."
            )

        raise NotImplementedError(
            f"GenAI provider '{self.provider}' "
            "integration is not implemented yet."
        )


genai_provider = GenAIProvider()