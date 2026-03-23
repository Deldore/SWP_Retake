from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.routes import router as api_router
from app.admin.routes import router as admin_router
from app.core.config import settings
from app.core.db import init_db

app = FastAPI(
    title="Poetry Conversational Recommender API",
    version="2.0.0",
    description="Backend for a Telegram bot that recommends English and Russian classic poems and tracks memorization without AI services.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def root():
    return RedirectResponse(url="/admin/")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(api_router, prefix="/api")
app.include_router(admin_router, prefix="/admin")
