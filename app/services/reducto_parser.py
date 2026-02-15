"""Parse resume via Reducto pipeline.

Returns structured resume dict: domain, yoe, country, skills[], summary.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.config.settings import settings

logger = logging.getLogger(__name__)


def _mimetype_from_filename(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return "application/pdf"
    if lower.endswith(".docx") or lower.endswith(".doc"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return "application/octet-stream"


def parse_resume_with_reducto(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Upload file to Reducto, run resume pipeline, return structured resume dict.

    Expected pipeline output shape: { domain, yoe, country, skills (list), summary }.
    """
    try:
        from reducto import Reducto
    except ImportError as e:
        raise ValueError(
            "reductoai package is not installed. pip install reductoai"
        ) from e

    api_key = (settings.REDUCTO_API_KEY or "").strip()
    if not api_key:
        raise ValueError(
            "REDUCTO_API_KEY is not set. Add it to your .env file."
        )

    pipeline_id = (settings.REDUCTO_PIPELINE_ID or "").strip()
    if not pipeline_id:
        raise ValueError(
            "REDUCTO_PIPELINE_ID is not set. Add it to your .env file."
        )

    client = Reducto(api_key=api_key)
    mimetype = _mimetype_from_filename(filename)
    upload = client.upload(file=(filename, file_bytes, mimetype))
    result = client.pipeline.run(input=upload.file_id, pipeline_id=pipeline_id)

    # PipelineResponse.result.extract.result is a list of extracted records (one per doc)
    extract_result = getattr(result, "result", None)
    extract_response = getattr(extract_result, "extract", None) if extract_result else None
    result_list = getattr(extract_response, "result", None) if extract_response else None

    if not result_list or not isinstance(result_list, list):
        raise ValueError("Reducto pipeline did not return extract result list.")

    # First record: Reducto uses "Domain", "Country", "Technical Skills", "Summary", "experience"
    print(result_list)
    data = result_list[0] if isinstance(result_list[0], dict) else {}
    domain = data.get("Domain") or data.get("domain") or "Engineering"
    yoe = data.get("experience") if "experience" in data else data.get("yoe")
    if yoe is None:
        yoe = 0
    try:
        yoe = int(yoe)
    except (TypeError, ValueError):
        yoe = 0
    country = data.get("Country") or data.get("country") or ""
    skills = data.get("Technical Skills") or data.get("skills")
    if not isinstance(skills, list):
        skills = []
    summary = data.get("Summary") or data.get("summary") or ""

    return {
        "domain": domain,
        "yoe": max(0, yoe),
        "country": country,
        "skills": skills,
        "summary": summary,
    }


def build_resume_meaning(domain: str, yoe: int, skills: List[str], summary: str) -> str:
    """Build the concatenated string used for resume embedding."""
    parts = [
        f"Domain: {domain}",
        f"Experience: {yoe}",
        f"Skills: {', '.join(skills) if skills else 'None'}",
        f"Summary: {summary}",
    ]
    return "\n".join(parts)
