import os

from app.llm.base import BaseLLM
from app.llm.config import settings
from app.llm.groq_provider import GroqProvider
from app.llm.ollama_provider import OllamaProvider


class LLMFactory:
    """Factory class to create provider-agnostic LLM instances.

    Determines the appropriate provider implementation based on environment configuration
    or explicit caller arguments without exposing provider details to business logic.
    """

    _PROVIDERS = {
        "groq": GroqProvider,
        "ollama": OllamaProvider,
    }

    @classmethod
    def get_provider(cls, provider_name: str | None = None) -> BaseLLM:
        """Instantiate and return an LLM provider based on configuration.

        Args:
            provider_name (str | None): Optional provider name override ('groq', 'ollama').
                Defaults to reading llm_provider from singleton settings.

        Returns:
            BaseLLM: An instance of a concrete LLM provider.

        Raises:
            ValueError: If llm_provider is not set or refers to an unsupported provider.
        """
        selected_provider = provider_name or settings.llm_provider

        if not selected_provider:
            raise ValueError("llm_provider configuration variable is not set.")

        provider_key = selected_provider.strip().lower()

        provider_cls = cls._PROVIDERS.get(provider_key)
        if not provider_cls:
            supported = ", ".join(f"'{p}'" for p in cls._PROVIDERS.keys())
            raise ValueError(
                f"Unsupported LLM provider '{selected_provider}'. "
                f"Supported providers are: {supported}."
            )

        return provider_cls()
