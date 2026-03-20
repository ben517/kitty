# AGENTS.md

This file provides guidance to Qoder (qoder.com) when working with code in this repository.

## Project Overview

SOS Demo - a smart home appliance Q&A system using RAG + multi-Agent architecture. Users can ask questions about device status, technical parameters, operation guides, and fault codes. The system retrieves from a local knowledge base (device manuals) and optionally queries live device data via Samsung SmartThings API.

## Build & Run Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start dev server (auto-reload)
./run.sh

# Or manually:
LD_LIBRARY_PATH=/nix/store/03h8f1wmpb86s9v8xd0lcb7jnp7nwm6l-idx-env-fhs/usr/lib:$LD_LIBRARY_PATH \
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Lint
flake8 app/
```

**Important**: This Nix-based environment requires `LD_LIBRARY_PATH` to be set for numpy/chromadb native libs. The `run.sh` script handles this automatically.

## Configuration

All settings use env vars with `SOS_` prefix, loaded via pydantic-settings from `.env`. See `.env.example` for all options.

LLM calls go through **litellm** using OpenAI-compatible format. Default config targets Alibaba DashScope (Qwen models):
- `SOS_LLM_MODEL=openai/qwen-turbo`
- `SOS_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`

## Architecture

```
app/
  main.py              # FastAPI app, lifespan, router registration
  config.py            # pydantic-settings (Settings singleton)
  models/
    schemas.py         # Pydantic request/response models, IntentType enum
  knowledge/
    parser.py          # Document parsing (PDF/Word/HTML/TXT via langchain loaders)
    processor.py       # Text cleaning + chunking (RecursiveCharacterTextSplitter)
    vectorstore.py     # ChromaDB persistent client, upsert/query operations
  rag/
    llm.py             # litellm wrappers: get_embedding(), chat_completion()
    retriever.py       # Multi-way recall: semantic_search + keyword_search -> merge + dedup
    reranker.py        # LLM-based re-ranking with relevance scoring
    generator.py       # Final answer generation with system prompt and context
  agents/
    orchestrator.py    # Intent recognition (LLM) -> route to device_info or general_qa
    device_info.py     # Handles device queries: RAG + live SmartThings API data
  api/
    smartthings.py     # Async httpx client for Samsung SmartThings REST API
  routers/
    chat.py            # POST /chat/ - main Q&A endpoint
    devices.py         # GET /devices/* - proxy to SmartThings API
    knowledge.py       # POST /knowledge/upload - ingest documents into vector store
```

### Request flow

1. `POST /chat/` receives `ChatRequest(query, device_id?, device_type?, session_id?)`
2. **OrchestratorAgent** classifies intent via LLM -> one of 6 `IntentType` values
3. Routes to **DeviceInfoAgent** (device-specific) or general RAG pipeline
4. RAG pipeline: `multi_recall()` (semantic + keyword) -> `rerank()` -> `generate_answer()`
5. DeviceInfoAgent additionally fetches live data from SmartThings API based on intent type
6. Returns `ChatResponse(answer, sources, device_id, session_id)`

### Key design decisions

- **litellm** abstracts LLM provider differences - switch models by changing env vars only
- **ChromaDB** in persistent mode stores vectors under `./data/chroma/`
- Session history is in-memory dict (`_sessions` in orchestrator.py) - needs Redis/DB for production
- Embedding and re-ranking share the same LLM config; reranker uses `temperature=0.0`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/chat/` | Main Q&A (orchestrator pipeline) |
| POST | `/knowledge/upload` | Upload device manual (multipart file + device_type) |
| GET | `/devices/` | List devices from SmartThings |
| GET | `/devices/{id}` | Get device info |
| GET | `/devices/{id}/status` | Get device status |
| GET | `/devices/{id}/health` | Get device health |
| GET | `/devices/{id}/capabilities` | Get device capabilities |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |
