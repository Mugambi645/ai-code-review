"""Anthropic (Claude) provider."""

import os
from typing import AsyncGenerator
import anthropic

from .base import BaseProvider


class AnthropicProvider(BaseProvider):
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-5")

    async def stream_review(
        self, system_prompt: str, user_prompt: str
    ) -> AsyncGenerator[str, None]:
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text
