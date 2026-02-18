from fastapi import APIRouter

from app.api.routes.chat import router as chat_router
from app.api.routes.documents import router as documents_router
from app.api.routes.ingestion_jobs import router as ingestion_jobs_router
from app.api.routes.llm import router as llm_router


api_router = APIRouter(prefix="/api")
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(ingestion_jobs_router, prefix="/ingestion-jobs", tags=["ingestion-jobs"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(llm_router, prefix="/llm", tags=["llm"])
