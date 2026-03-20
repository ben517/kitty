"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # SmartThings API
    smartthings_base_url: str = "https://api.samsungiotcloud.cn"
    smartthings_token: str = ""
    smartthings_location_id: str = ""

    # LLM (via litellm, use "openai/<model>" format with api_base for self-hosted)
    # For DashScope (Alibaba Cloud): model="openai/qwen-turbo", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "openai/qwen-turbo"
    llm_api_key: str = ""
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Embedding
    embedding_model: str = "openai/text-embedding-v3"
    embedding_api_key: str = ""
    embedding_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    embedding_dimension: int = 1024

    # ChromaDB
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection_name: str = "device_knowledge"

    # RAG
    rag_top_k: int = 5
    rag_rerank_top_n: int = 3
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 50

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "env_prefix": "SOS_"}


settings = Settings()
