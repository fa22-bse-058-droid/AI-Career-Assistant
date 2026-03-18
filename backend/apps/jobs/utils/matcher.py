"""
Matching engine: compute cosine-similarity scores between CV text and job descriptions.

Performance note: batch_compute_matches() encodes all job descriptions in a single
model.encode() call, which is ~50x faster than encoding them one-by-one.
"""
import logging

import numpy as np

_MATCH_BATCH_SIZE = 64  # number of job texts to encode in one batch call
_model = None


def get_model():
    """Load and cache the SentenceTransformer model (one instance per process)."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("SentenceTransformer 'all-MiniLM-L6-v2' loaded in matcher module")
        except Exception as exc:
            logger.error("Failed to load SentenceTransformer: %s", exc)
            _model = None
    return _model


def compute_cosine_similarity(text1: str, text2: str) -> float:
    """Encode two texts and return their cosine similarity (0.0 – 1.0)."""
    model = get_model()
    if model is None:
        return 0.0
    try:
        emb1, emb2 = model.encode([text1, text2])
        dot = float(np.dot(emb1, emb2))
        norm = float(np.linalg.norm(emb1) * np.linalg.norm(emb2))
        if norm == 0:
            return 0.0
        return max(0.0, min(1.0, dot / norm))
    except Exception as exc:
        logger.error("compute_cosine_similarity error: %s", exc)
        return 0.0


def _get_match_label(score: float) -> str:
    if score >= 0.80:
        return "Excellent"
    if score >= 0.65:
        return "Good"
    if score >= 0.50:
        return "Fair"
    return "Low"


def compute_match_score(
    cv_text: str,
    job_description: str,
    cv_skills: list | None = None,
    job_skills: list | None = None,
) -> dict:
    """
    Compute a combined match score for one job.

    Returns a dict with:
      score, skill_overlap, skill_overlap_count, match_label, is_auto_apply_eligible
    """
    score = compute_cosine_similarity(cv_text, job_description)

    skill_overlap: list = []
    if cv_skills and job_skills:
        cv_set = {s.lower() for s in cv_skills}
        job_set = {s.lower() for s in job_skills}
        skill_overlap = sorted(cv_set & job_set)

    return {
        "score": round(score, 4),
        "skill_overlap": skill_overlap,
        "skill_overlap_count": len(skill_overlap),
        "match_label": _get_match_label(score),
        "is_auto_apply_eligible": score >= 0.65,
    }


def batch_compute_matches(
    cv_text: str,
    jobs_queryset,
    cv_skills: list | None = None,
) -> list[dict]:
    """
    Batch-compute match scores for all jobs in queryset.

    Encodes CV text once and all job descriptions in a single batch call —
    this is the performance-critical path.

    Returns a list of dicts:
      [{job_id, score, skill_overlap, skill_overlap_count, match_label, is_auto_apply_eligible}, ...]
    """
    model = get_model()
    if model is None:
        return []

    jobs = list(
        jobs_queryset.values("id", "title", "description", "skills_required")
    )
    if not jobs:
        return []

    try:
        cv_embedding = model.encode(cv_text, convert_to_numpy=True)

        job_texts = [
            f"{j['title']} {j['description']}" for j in jobs
        ]
        job_embeddings = model.encode(job_texts, convert_to_numpy=True, batch_size=_MATCH_BATCH_SIZE)

        # Vectorised cosine similarity
        cv_norm = np.linalg.norm(cv_embedding)
        job_norms = np.linalg.norm(job_embeddings, axis=1)
        dots = job_embeddings @ cv_embedding

        with np.errstate(divide="ignore", invalid="ignore"):
            similarities = np.where(
                (cv_norm * job_norms) > 0,
                dots / (cv_norm * job_norms),
                0.0,
            )
        similarities = np.clip(similarities, 0.0, 1.0)

        cv_skill_set = {s.lower() for s in (cv_skills or [])}

        results = []
        for idx, job in enumerate(jobs):
            score = float(similarities[idx])
            job_skills = [s.lower() for s in (job.get("skills_required") or [])]
            overlap = sorted(cv_skill_set & set(job_skills)) if cv_skill_set else []

            results.append({
                "job_id": job["id"],
                "score": round(score, 4),
                "skill_overlap": overlap,
                "skill_overlap_count": len(overlap),
                "match_label": _get_match_label(score),
                "is_auto_apply_eligible": score >= 0.65,
            })

        return results

    except Exception as exc:
        logger.error("batch_compute_matches error: %s", exc)
        return []
