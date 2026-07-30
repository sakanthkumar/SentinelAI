from abc import ABC, abstractmethod
from typing import Any


class BaseLLM(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    def generate(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            messages: Chat messages in OpenAI format.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated response text.
        """
        raise NotImplementedError

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Return the active model name.
        """
        raise NotImplementedError