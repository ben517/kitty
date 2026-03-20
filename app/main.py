"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.smartthings import smartthings
from app.routers import chat, devices, knowledge

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.getLogger(__name__).info("SOS Demo starting up")
    yield
    # Shutdown
    await smartthings.close()
    logging.getLogger(__name__).info("SOS Demo shut down")


app = FastAPI(
    title="SOS Demo - 家电智能问答系统",
    description="基于 RAG + 多 Agent 架构的家用电器智能问答服务",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(chat.router)
app.include_router(devices.router)
app.include_router(knowledge.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
