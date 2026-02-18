from fastapi import APIRouter

from app.settings import settings


router = APIRouter()


@router.get("/providers")
async def list_providers() -> dict:
    items = [
        {"provider": "openai_compat", "models": [settings.default_llm_model]},
        {"provider": "ollama", "models": [settings.ollama_model]},
    ]
    return {"items": items}
