"""Provider factory — swap AI providers via AI_PROVIDER env var."""

import os
from .base import BaseProvider


def get_provider() -> BaseProvider:
    """
    Return the configured AI provider.

    Set AI_PROVIDER to one of:
        anthropic   → Claude (default)
        openai      → GPT-4o
        huggingface → HuggingFace Inference API
    """
    provider = os.getenv("AI_PROVIDER", "anthropic").lower()

    if provider == "anthropic":
        from .anthropic_provider import AnthropicProvider
        return AnthropicProvider()

    elif provider == "openai":
        from .openai_provider import OpenAIProvider
        return OpenAIProvider()

    elif provider == "huggingface":
        from .huggingface_provider import HuggingFaceProvider
        return HuggingFaceProvider()

    else:
        raise ValueError(
            f"Unknown AI_PROVIDER '{provider}'. "
            "Choose from: anthropic, openai, huggingface"
        )
