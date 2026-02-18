from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.settings import settings


@dataclass(frozen=True)
class EmbeddingsResult:
    vectors: list[list[float]]
    model: str


async def embed_texts(texts: list[str]) -> EmbeddingsResult:
    if settings.embeddings_provider == "ollama":
        vectors: list[list[float]] = []
        async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=60.0) as client:
            for t in texts:
                resp = await client.post("/api/embeddings", json={"model": settings.embeddings_model, "prompt": t})
                resp.raise_for_status()
                data = resp.json()
                vectors.append(data["embedding"])
        return EmbeddingsResult(vectors=vectors, model=settings.embeddings_model)

    if settings.embeddings_provider == "openai_compat":
        if not settings.openai_compat_api_key:
            raise RuntimeError("OPENAI_COMPAT_API_KEY is required for openai_compat embeddings")
        headers = {"Authorization": f"Bearer {settings.openai_compat_api_key}"}
        async with httpx.AsyncClient(base_url=settings.openai_compat_base_url, timeout=60.0, headers=headers) as client:
            resp = await client.post(
                "/embeddings",
                json={"model": settings.embeddings_model, "input": texts},
            )
            resp.raise_for_status()
            data = resp.json()
            vectors = [item["embedding"] for item in data["data"]]
            return EmbeddingsResult(vectors=vectors, model=settings.embeddings_model)

    raise RuntimeError(f"Unsupported embeddings_provider: {settings.embeddings_provider}")
