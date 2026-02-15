"""Semantic search over job embeddings in Postgres (pgvector). Full-table ANN only."""

from __future__ import annotations

from typing import List, Tuple

from sqlalchemy.orm import Session

from app.models.job import Job


def query_similar_jobs_postgres_full_table(
    db: Session,
    resume_embedding: List[float],
    top_k: int,
) -> List[Tuple[str, float]]:
    """Full-table ANN: top_k jobs by cosine similarity to resume_embedding (no ID filter).

    Uses HNSW index. Returns list of (job_id, similarity_score).
    """
    if resume_embedding is None or len(resume_embedding) == 0 or top_k <= 0:
        return []

    vec = [float(x) for x in resume_embedding]
    from pgvector import Vector
    from pgvector.psycopg2 import register_vector
    raw_conn = db.connection().connection
    register_vector(raw_conn, globally=True)
    vec_param = Vector(vec)

    sql = """
        SELECT id, (1 - (job_embedding <=> %s)) AS score
        FROM jobs
        WHERE job_embedding IS NOT NULL
        ORDER BY job_embedding <=> %s
        LIMIT %s
    """
    with raw_conn.cursor() as cursor:
        cursor.execute(sql, (vec_param, vec_param, top_k))
        rows = cursor.fetchall()

    return [(row[0], float(row[1])) for row in rows]


def load_jobs_with_semantic_scores_full_table(
    db: Session,
    resume_embedding: List[float],
    top_k: int,
) -> Tuple[List[Job], dict]:
    """Full-table ANN: load top_k jobs by similarity and return (jobs, job_id -> score)."""
    similar = query_similar_jobs_postgres_full_table(
        db, resume_embedding, top_k=top_k
    )
    if not similar:
        return [], {}

    ids_ordered = [jid for jid, _ in similar]
    scores = {jid: score for jid, score in similar}

    jobs = db.query(Job).filter(Job.id.in_(ids_ordered)).all()
    id_to_job = {j.id: j for j in jobs}
    ordered_jobs = [id_to_job[jid] for jid in ids_ordered if jid in id_to_job]

    return ordered_jobs, scores
