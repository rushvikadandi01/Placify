import asyncio
import json
import socket
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request as URLRequest
from urllib.request import urlopen

from ..config import settings


class AIServiceError(Exception):
    """Base error for AI provider failures."""


class AIConfigurationError(AIServiceError):
    """Raised when an enabled provider is missing required settings."""


class AIProviderTimeoutError(AIServiceError):
    """Raised when an AI provider request times out."""


class AIProviderError(AIServiceError):
    """Raised when an AI provider request fails or returns invalid data."""


class AIProvider(Protocol):
    async def generate_response(self, system_prompt: str, user_message: str) -> str:
        ...


class OpenAICompatibleProvider:
    def __init__(self, api_key: str, model: str, base_url: str, timeout_seconds: float = 30):
        self.api_key = api_key
        self.model = model
        self.endpoint = f"{base_url.rstrip('/')}/chat/completions"
        self.timeout_seconds = timeout_seconds

    async def generate_response(self, system_prompt: str, user_message: str) -> str:
        return await asyncio.to_thread(self._generate_response, system_prompt, user_message)

    def _generate_response(self, system_prompt: str, user_message: str) -> str:
        body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            }
        ).encode("utf-8")
        request = URLRequest(
            self.endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            raise AIProviderError(f"The AI provider returned HTTP {error.code}.") from None
        except (TimeoutError, socket.timeout):
            raise AIProviderTimeoutError("The AI provider request timed out.") from None
        except URLError as error:
            if isinstance(error.reason, (TimeoutError, socket.timeout)):
                raise AIProviderTimeoutError("The AI provider request timed out.") from None
            raise AIProviderError("Could not connect to the AI provider.") from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise AIProviderError("The AI provider returned an invalid response.") from None

        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise AIProviderError("The AI provider response did not contain a message.") from None

        if not isinstance(content, str) or not content.strip():
            raise AIProviderError("The AI provider returned an empty message.")
        return content.strip()


def _configured_provider() -> AIProvider | None:
    has_ai_settings = any(
        (settings.ai_provider, settings.ai_api_key, settings.ai_model, settings.ai_base_url)
    )
    if not has_ai_settings:
        return None

    provider_name = (settings.ai_provider or "openai-compatible").lower().replace("_", "-")
    if provider_name not in ("openai", "openai-compatible"):
        raise AIConfigurationError("AI_PROVIDER must be set to 'openai_compatible' for this provider.")
    if not settings.ai_api_key:
        raise AIConfigurationError("AI_API_KEY is required when an AI provider is configured.")
    if not settings.ai_model:
        raise AIConfigurationError("AI_MODEL is required when an AI provider is configured.")

    return OpenAICompatibleProvider(
        api_key=settings.ai_api_key,
        model=settings.ai_model,
        base_url=settings.ai_base_url or "https://api.openai.com/v1",
    )


class AIService:
    def __init__(self, provider: AIProvider | None = None):
        self.provider = provider

    async def generate_response(self, system_prompt: str, user_message: str) -> str | None:
        provider = self.provider or _configured_provider()
        if provider is None:
            return None
        return await provider.generate_response(system_prompt, user_message)


ai_service = AIService()