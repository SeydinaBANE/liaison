"""Adapter LLM HTTP asynchrone compatible chat completions (LiteLLM/OpenAI)."""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx

from liaison.domain.models import LLMRequest
from liaison.ports.llm import LLMProviderError


class HttpLLMProvider:
    """Provider HTTP asynchrone compatible chat completions (LiteLLM/OpenAI)."""

    def __init__(
        self, model: str, client: httpx.AsyncClient, path: str = "/chat/completions"
    ) -> None:
        self.model = model
        self._client = client
        self._path = path

    def _build_payload(self, request: LLMRequest) -> dict[str, object]:
        return {
            "model": self.model,
            "messages": [{"role": m.role.value, "content": m.content} for m in request.messages],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

    async def complete(self, request: LLMRequest) -> str:
        payload = self._build_payload(request)
        try:
            response = await self._client.post(self._path, json=payload)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"appel LLM {self.model} echoue: {exc}") from exc
        try:
            return str(response.json()["choices"][0]["message"]["content"])
        except (KeyError, IndexError, ValueError) as exc:
            raise LLMProviderError(f"reponse LLM {self.model} invalide: {exc}") from exc

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        payload = self._build_payload(request)
        payload["stream"] = True
        try:
            async with self._client.stream("POST", self._path, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or line == "data: [DONE]":
                        continue
                    if line.startswith("data: "):
                        import json as _json

                        chunk = _json.loads(line[6:])
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content: str = delta.get("content", "")
                        if content:
                            yield content
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"stream LLM {self.model} echoue: {exc}") from exc
