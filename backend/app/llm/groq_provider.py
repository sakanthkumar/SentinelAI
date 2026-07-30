import logging
from typing import Any

from groq import Groq

from app.llm.base import BaseLLM
from app.llm.config import settings

logger = logging.getLogger(__name__)


class GroqProvider(BaseLLM):
    """Groq Cloud API provider implementation."""

    def __init__(self, model_name: str | None = None) -> None:
        """
        Initialize Groq client using project configuration.
        """
        api_key = settings.groq_api_key

        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured.")

        self.model_name = model_name or settings.groq_model
        self.client = Groq(api_key=api_key)

    def generate(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> str:
        """
        Generate a response using Groq Chat Completions API.

        Args:
            messages: Chat messages.
            temperature: Sampling temperature.
            max_tokens: Maximum output tokens.

        Returns:
            Generated response text.
        """
        if not messages:
            raise ValueError("Messages cannot be empty.")

        try:
            logger.info(
                "Sending request to Groq using model '%s'...",
                self.model_name,
            )

            request_kwargs = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens is not None:
                request_kwargs["max_tokens"] = max_tokens

            response = self.client.chat.completions.create(**request_kwargs)

            return response.choices[0].message.content or ""

        except Exception as exc:
            logger.exception("Groq API request failed.")
            raise RuntimeError(
                f"Groq API text generation failed: {exc}"
            ) from exc

    def get_model_name(self) -> str:
        """
        Return the configured model name.
        """
        return self.model_name