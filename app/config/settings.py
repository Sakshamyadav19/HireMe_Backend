from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Existing ──
    DATABASE_URL: str

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def strip_database_url_quotes(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().strip('"').strip("'")
        return v
    JWT_SECRET: str
    FRONTEND_URL: str = "http://localhost:8080"

    # ── LLM (OpenRouter) ──
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "google/gemini-2.5-flash"

    # ── Embeddings (OpenRouter, same key as LLM) ──
    EMBEDDING_MODEL: str = "openai/text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536

    # ── Reducto (resume parsing pipeline) ──
    REDUCTO_API_KEY: str = ""
    REDUCTO_PIPELINE_ID: str = "k9768yn3q9sfczr46t0red1dg18153rk"

    # ── Matching (Postgres + pgvector) ──
    YOE_WINDOW: int = 4  # ±years for display
    ANN_TOP_K: int = 200
    ANN_CANDIDATE_POOL: int = 5000  # Vector-first: fetch this many by similarity, then filter by domain/YoE/country
    WEIGHT_SKILLS: float = 0.45
    WEIGHT_SEMANTIC: float = 0.40
    WEIGHT_YOE: float = 0.15

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
