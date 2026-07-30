import logging
from typing import Any

import ollama

from app.llm.base import BaseLLM
from app.llm.config import settings

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLM):
    """Ollama local LLM provider implementation."""

    def __init__(self, model_name: str | None = None) -> None:
        """
        Initialize Ollama provider.
        """
        self.model_name = model_name or settings.ollama_model

    def generate(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> str:
        """
        Generate a response using the local Ollama server.

        Args:
            messages: Chat messages in OpenAI format.
            temperature: Sampling temperature.
            max_tokens: Maximum output tokens.

        Returns:
            Generated response text.
        """
        if not messages:
            raise ValueError("Messages cannot be empty.")

        try:
            logger.info(
                "Sending request to Ollama using model '%s'...",
                self.model_name,
            )

            request_kwargs = {
                "model": self.model_name,
                "messages": messages,
                "options": {
                    "temperature": temperature,
                },
            }

            if max_tokens is not None:
                request_kwargs["options"]["num_predict"] = max_tokens

            response = ollama.chat(**request_kwargs)

            return response["message"]["content"]

        except Exception as exc:
            logger.exception("Ollama generation failed.")
            raise RuntimeError(
                f"Ollama text generation failed: {exc}"
            ) from exc

    def get_model_name(self) -> str:
        """
        Return the active model name.
        """
        return self.model_name