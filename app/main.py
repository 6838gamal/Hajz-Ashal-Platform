from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.database import engine
from app.module_registry import register_all_modules
from app.settings import get_settings
from app.web_routes import router as web_router
from core.presentation.error_handlers import register_error_handlers
from core.presentation.middlewares import RequestIdMiddleware, TenantContextMiddleware

settings = get_settings()

app = FastAPI(title="حجز أسهل", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TenantContextMiddleware)
app.add_middleware(RequestIdMiddleware)

register_error_handlers(app)
register_all_modules(app)
app.include_router(web_router)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
async def health_ready():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ready"}
