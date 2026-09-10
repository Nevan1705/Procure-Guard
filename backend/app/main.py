"""ProcureGuard FastAPI application entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.db.base import Base, SessionLocal, engine
from app.db import models  # noqa: F401 — ensure models are registered

app = FastAPI(
    title="ProcureGuard API",
    version="0.1.0",
    description="AI-powered bid compliance verification for GeM procurement (SIH 2026 prototype).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
def on_startup() -> None:
    """Create tables on startup (MVP; Alembic migrations come with Postgres)."""
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "procureguard", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
