"""FastAPI application entry point."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.smartthings import smartthings
from app.routers import chat, devices, knowledge

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.getLogger(__name__).info("System starting up")
    yield
    # Shutdown
    await smartthings.close()
    logging.getLogger(__name__).info("System shut down")


app = FastAPI(
    title="家电智能问答系统",
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


# Serve web-chat frontend static files
web_chat_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web-chat")
if os.path.exists(web_chat_dir):
    app.mount("/static", StaticFiles(directory=web_chat_dir), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(web_chat_dir, "index.html"))
