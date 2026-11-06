"""
Application configuration — reads all settings from environment variables.
Never hardcode credentials here. Use .env locally (never committed).
"""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All application settings sourced exclusively from environment variables.
    See .env.example for the full list and descriptions.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    app_name: str = "Smart Farming AI"
    app_version: str = "1.0.0"
    debug: bool = False
    allowed_origins: str = "http://localhost:5173"  # comma-separated

    # ── IBM watsonx.ai / Granite ──────────────────────────────────────────────
    # Credentials — must be set in .env, never hardcoded
    watsonx_api_key: Optional[str] = None
    watsonx_project_id: Optional[str] = None
    watsonx_url: str = "https://us-south.ml.cloud.ibm.com"

    # Model selection — fully configurable via GRANITE_MODEL_ID env var.
    #
    # IMPORTANT — model availability on IBM Cloud Lite (us-south), as of 2026:
    #
    #   ibm/granite-4-h-small          ✅ ACTIVE  — direct inference, Lite-accessible,
    #                                               30B params, launched Oct 2025.
    #                                               This is the recommended default.
    #
    #   ibm/granite-3-3-8b-instruct    ❌ WITHDRAWN — deprecated Nov 2025,
    #                                               withdrawn Feb 22 2026.
    #
    #   ibm/granite-3-8b-instruct      ❌ WITHDRAWN — deprecated Nov 2025,
    #                                               withdrawn Feb 22 2026.
    #
    #   ibm/granite-4-h-small-curated  ❌ NOT LITE — deploy-on-demand only,
    #                                               requires paid plan + deployment.
    #
    # The default is ibm/granite-4-h-small.  Override via GRANITE_MODEL_ID in .env.
    # The application will NEVER substitute another LLM — if Granite is unavailable,
    # it will return a clear error rather than falling back to a different model.
    granite_model_id: str = "ibm/granite-4-h-small"

    # Granite inference defaults — all configurable via env vars
    granite_max_new_tokens: int = 512
    granite_min_new_tokens: int = 10
    granite_temperature: float = 0.7
    granite_top_p: float = 0.9
    granite_top_k: int = 50
    granite_repetition_penalty: float = 1.1

    # ── RAG / Embeddings ──────────────────────────────────────────────────────
    # Embedding model — configurable via EMBEDDING_MODEL env var.
    #
    # Default: sentence-transformers/LaBSE
    #   - Language-agnostic BERT Sentence Embeddings (Google, 2020)
    #   - Trained on 109 languages including Tamil (ISO 639-1: ta) and English
    #   - 768-dimensional embeddings; strong cross-lingual retrieval performance
    #   - Recommended for evaluating Tamil and English agricultural query retrieval
    #
    # Alternative (lighter, faster):
    #   sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
    #   - 50+ languages including Tamil; 384-dimensional; lower memory footprint
    #
    # Override via EMBEDDING_MODEL in .env to swap without code changes.
    embedding_model: str = "sentence-transformers/LaBSE"

    faiss_index_path: str = "data/faiss_index"
    documents_path: str = "data/documents"
    seed_docs_path: str = "data/seed_docs"
    rag_top_k: int = 3  
    rag_min_similarity: float = 0.30        # number of chunks to retrieve per query
    chunk_size: int = 300       # characters per document chunk
    chunk_overlap: int = 60     # character overlap between chunks

    # ── External APIs ─────────────────────────────────────────────────────────
    openweather_api_key: Optional[str] = None
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5"
    datagov_api_key: Optional[str] = None
    datagov_base_url: str = "https://api.data.gov.in/resource"
    # Agmarknet resource ID for mandi prices (commodity prices dataset)
    agmarknet_resource_id: str = "9ef84268-d588-465a-a308-a864a43d0070"

    # ── Cache TTLs ────────────────────────────────────────────────────────────
    weather_cache_ttl_seconds: int = 600   # 10 minutes
    mandi_cache_ttl_seconds: int = 3600    # 1 hour

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def granite_is_configured(self) -> bool:
        return bool(self.watsonx_api_key and self.watsonx_project_id)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
