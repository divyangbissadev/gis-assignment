"""
LLM Provider abstraction for NLP Query Parser.

Supports multiple LLM providers: Anthropic (Claude), OpenAI (GPT), and Google (Gemini).
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from enum import Enum

from src.errors import ArcGISValidationError
from src.logger import get_logger

logger = get_logger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM provider.

        Args:
            api_key: API key for the provider. If not provided, looks for environment variable.
        """
        self.api_key = api_key or self._get_api_key_from_env()
        if not self.api_key:
            raise ArcGISValidationError(
                f"{self.provider_name} API key required. Set {self.env_var_name} environment variable "
                f"or pass api_key parameter."
            )

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name."""
        pass

    @property
    @abstractmethod
    def env_var_name(self) -> str:
        """Environment variable name for API key."""
        pass

    @abstractmethod
    def _get_api_key_from_env(self) -> Optional[str]:
        """Get API key from environment variable."""
        pass

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 1024) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: The prompt to send to the LLM.
            max_tokens: Maximum tokens in the response.

        Returns:
            The LLM's text response.

        Raises:
            ArcGISValidationError: If the API call fails.
        """
        pass


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider."""

    @property
    def provider_name(self) -> str:
        return "Anthropic Claude"

    @property
    def env_var_name(self) -> str:
        return "ANTHROPIC_API_KEY"

    def _get_api_key_from_env(self) -> Optional[str]:
        return os.environ.get("ANTHROPIC_API_KEY")

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-5-20250929"):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key.
            model: Claude model to use (default: claude-sonnet-4-5-20250929).
        """
        super().__init__(api_key)
        self.model = model

        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
            logger.info(f"Anthropic provider initialized", extra={"model": self.model})
        except ImportError:
            raise ArcGISValidationError(
                "anthropic package not installed. Install with: pip install anthropic"
            )

    def generate(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate response using Claude."""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error", extra={"error": str(e)})
            raise ArcGISValidationError(f"Anthropic API error: {e}") from e


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider."""

    @property
    def provider_name(self) -> str:
        return "OpenAI GPT"

    @property
    def env_var_name(self) -> str:
        return "OPENAI_API_KEY"

    def _get_api_key_from_env(self) -> Optional[str]:
        return os.environ.get("OPENAI_API_KEY")

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key.
            model: GPT model to use (default: gpt-4o).
        """
        super().__init__(api_key)
        self.model = model

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"OpenAI provider initialized", extra={"model": self.model})
        except ImportError:
            raise ArcGISValidationError(
                "openai package not installed. Install with: pip install openai"
            )

    def generate(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate response using GPT."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error", extra={"error": str(e)})
            raise ArcGISValidationError(f"OpenAI API error: {e}") from e


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider."""

    @property
    def provider_name(self) -> str:
        return "Google Gemini"

    @property
    def env_var_name(self) -> str:
        return "GEMINI_API_KEY"

    def _get_api_key_from_env(self) -> Optional[str]:
        return os.environ.get("GEMINI_API_KEY")

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash"):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google API key.
            model: Gemini model to use (default: gemini-2.0-flash-exp).
        """
        super().__init__(api_key)
        self.model = model

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
            logger.info(f"Gemini provider initialized", extra={"model": self.model})
        except ImportError:
            raise ArcGISValidationError(
                "google-generativeai package not installed. Install with: pip install google-generativeai"
            )

    def generate(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate response using Gemini."""
        try:
            response = self.client.generate_content(
                prompt,
                generation_config={"max_output_tokens": max_tokens, "temperature": 0.7}
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error", extra={"error": str(e)})
            raise ArcGISValidationError(f"Gemini API error: {e}") from e


def create_provider(
    provider: str = "anthropic",
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> BaseLLMProvider:
    """
    Factory function to create an LLM provider.

    Args:
        provider: Provider name ("anthropic", "openai", or "gemini").
        api_key: API key for the provider (optional, uses env var if not provided).
        model: Model name (optional, uses provider default if not provided).

    Returns:
        Initialized provider instance.

    Raises:
        ArcGISValidationError: If provider is not supported or initialization fails.

    Examples:
        >>> provider = create_provider("anthropic")
        >>> provider = create_provider("openai", model="gpt-4")
        >>> provider = create_provider("gemini", api_key="your-key")
    """
    provider = provider.lower()

    if provider == LLMProvider.ANTHROPIC:
        kwargs = {"api_key": api_key}
        if model:
            kwargs["model"] = model
        return AnthropicProvider(**kwargs)

    elif provider == LLMProvider.OPENAI:
        kwargs = {"api_key": api_key}
        if model:
            kwargs["model"] = model
        return OpenAIProvider(**kwargs)

    elif provider == LLMProvider.GEMINI:
        kwargs = {"api_key": api_key}
        if model:
            kwargs["model"] = model
        return GeminiProvider(**kwargs)

    else:
        raise ArcGISValidationError(
            f"Unsupported provider: {provider}. Supported providers: {', '.join([p.value for p in LLMProvider])}"
        )


def get_available_providers() -> Dict[str, Dict[str, Any]]:
    """
    Get information about available LLM providers.

    Returns:
        Dictionary with provider information including default models and env vars.
    """
    return {
        "anthropic": {
            "name": "Anthropic Claude",
            "default_model": "claude-sonnet-4-5-20250929",
            "env_var": "ANTHROPIC_API_KEY",
            "signup_url": "https://console.anthropic.com/",
            "models": [
                "claude-sonnet-4-5-20250929",
                "claude-opus-4-5-20250229",
                "claude-3-5-sonnet-20241022"
            ]
        },
        "openai": {
            "name": "OpenAI GPT",
            "default_model": "gpt-4o",
            "env_var": "OPENAI_API_KEY",
            "signup_url": "https://platform.openai.com/signup",
            "models": [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-3.5-turbo"
            ]
        },
        "gemini": {
            "name": "Google Gemini",
            "default_model": "gemini-2.0-flash",
            "env_var": "GEMINI_API_KEY",
            "signup_url": "https://makersuite.google.com/app/apikey",
            "models": [
                "gemini-2.0-flash",
                "gemini-1.5-flash",
                "gemini-1.5-pro-latest",
                "gemini-pro"
            ]
        }
    }
