"""Generate embeddings via OpenRouter (OpenAI-compatible embeddings API).

Used for:
- Embedding job_meaning at ingest time → stored in Postgres (pgvector)
- Embedding resume_meaning at upload time → stored in Postgres (pgvector)
"""

from __future__ import annotations

import logging
from typing import List

import httpx

from app.config.settings import settings

logger = logging.getLogger(__name__)

OPENROUTER_EMBEDDINGS_URL = "https://openrouter.ai/api/v1/embeddings"


async def embed_text(text: str) -> List[float]:
    """Embed a single text string and return the vector."""
    return (await embed_texts([text]))[0]


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed multiple texts in a single API call (batch) via OpenRouter."""
    if not texts:
        return []

    api_key = (settings.OPENROUTER_API_KEY or "").strip()
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not set. Add it to your .env file (see .env.example)."
        )
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.EMBEDDING_MODEL,
        "input": texts,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            OPENROUTER_EMBEDDINGS_URL,
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()

    data = resp.json()
    # Sort by index to preserve order (OpenRouter returns same shape as OpenAI)
    embeddings = sorted(data["data"], key=lambda x: x["index"])
    vectors = [item["embedding"] for item in embeddings]

    logger.info("Embedded %d text(s), dimension=%d", len(vectors), len(vectors[0]) if vectors else 0)
    return vectors


def build_job_meaning(
    title: str,
    domain: str,
    subdomain: str,
    years_experience_min: int,
    skills_required: list,
    description: str,
) -> str:
    """Build the single string used for job embedding (stored as job_meaning)."""
    domain_line = f"{domain} / {subdomain}" if subdomain else domain
    skills_csv = ", ".join(skills_required) if skills_required else "None"
    summary = (description or "")[:1200]
    parts = [
        f"Title: {title}",
        f"Domain: {domain_line}",
        f"Experience: {years_experience_min}+ years",
        f"Skills: {skills_csv}",
        f"Summary: {summary}",
    ]
    return "\n".join(parts)


def build_resume_embedding_text(
    domain: str,
    subdomain: str,
    skills: list,
    resume_text: str,
) -> str:
    """Legacy: build text for resume embedding. Prefer reducto_parser.build_resume_meaning."""
    parts = [f"Domain: {domain}"]
    if subdomain:
        parts.append(f"Subdomain: {subdomain}")
    if skills:
        parts.append(f"Skills: {', '.join(skills)}")
    if resume_text:
        parts.append(f"Experience: {resume_text[:3000]}")
    return "\n".join(parts)
