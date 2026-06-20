"""Base interface for all AI providers."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator


class BaseProvider(ABC):
    """All AI providers must implement this interface."""

    @abstractmethod
    async def stream_review(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> AsyncGenerator[str, None]:
        """Stream a code review response token by token."""
        ...

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Return a complete (non-streaming) response."""
        ...
