import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.routes.health import router as health_router
from app.db_init import init_db
from app.settings import settings


logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)

@app.on_event("startup")
async def _startup() -> None:
    try:
        await init_db()
    except Exception:
        logger.exception("Database init failed")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(health_router)
