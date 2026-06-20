"""HuggingFace Inference API provider."""

import os
from typing import AsyncGenerator
import httpx

from .base import BaseProvider


class HuggingFaceProvider(BaseProvider):
    def __init__(self):
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.model = os.getenv(
            "HUGGINGFACE_MODEL", "codellama/CodeLlama-34b-Instruct-hf"
        )
        self.base_url = f"https://api-inference.huggingface.co/models/{self.model}"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def _build_prompt(self, system_prompt: str, user_prompt: str) -> str:
        """Format prompt for instruction-tuned models."""
        return f"[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{user_prompt} [/INST]"

    async def stream_review(
        self, system_prompt: str, user_prompt: str
    ) -> AsyncGenerator[str, None]:
        # HuggingFace streaming via text-generation endpoint
        prompt = self._build_prompt(system_prompt, user_prompt)
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": 2048, "return_full_text": False},
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST", self.base_url, json=payload, headers=self.headers
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        if data and data != "[DONE]":
                            import json
                            try:
                                token = json.loads(data).get("token", {}).get("text", "")
                                if token:
                                    yield token
                            except Exception:
                                pass

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        prompt = self._build_prompt(system_prompt, user_prompt)
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": 2048, "return_full_text": False},
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                self.base_url, json=payload, headers=self.headers
            )
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                return data[0].get("generated_text", "")
            return data.get("generated_text", "")
