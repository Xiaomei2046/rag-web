from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.settings import settings


@dataclass(frozen=True)
class ChatUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass(frozen=True)
class ChatResult:
    content: str
    usage: ChatUsage


async def chat_complete(
    *,
    provider: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
) -> ChatResult:
    if provider == "ollama":
        async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=120.0) as client:
            resp = await client.post(
                "/api/chat",
                json={"model": model or settings.ollama_model, "messages": messages, "stream": False, "options": {"temperature": temperature}},
            )
            resp.raise_for_status()
            data = resp.json()
            return ChatResult(content=str(data["message"]["content"]), usage=ChatUsage())

    if provider == "openai_compat":
        if not settings.openai_compat_api_key:
            raise RuntimeError("OPENAI_COMPAT_API_KEY is required for openai_compat chat")
        headers = {"Authorization": f"Bearer {settings.openai_compat_api_key}"}
        async with httpx.AsyncClient(base_url=settings.openai_compat_base_url, timeout=120.0, headers=headers) as client:
            resp = await client.post(
                "/chat/completions",
                json={"model": model or settings.default_llm_model, "messages": messages, "temperature": temperature},
            )
            resp.raise_for_status()
            data = resp.json()
            content = str(data["choices"][0]["message"]["content"])
            usage_data = data.get("usage") or {}
            usage = ChatUsage(
                prompt_tokens=int(usage_data.get("prompt_tokens") or 0),
                completion_tokens=int(usage_data.get("completion_tokens") or 0),
                total_tokens=int(usage_data.get("total_tokens") or 0),
            )
            return ChatResult(content=content, usage=usage)

    raise RuntimeError(f"Unsupported provider: {provider}")
