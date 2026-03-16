"""
Celery tasks for CV Analyzer.
"""
import logging
import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

FASTAPI_BASE_URL = getattr(settings, "AI_SERVICE_URL", "http://fastapi:8001")


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
    name="cv_analyzer.analyze_cv",
)
def analyze_cv_task(self, cv_upload_id: str):
    """
    Asynchronously analyze an uploaded CV:
    1. Extract text from PDF/DOCX
    2. Extract skills using PhraseMatcher
    3. Score the CV
    4. Detect skill gaps
    5. Call FastAPI deep analysis endpoint
    6. Save CVAnalysis
    """
    from .models import CVUpload, CVAnalysis
    from .analyzer import (
        extract_text_from_pdf,
        extract_text_from_docx,
        validate_magic_bytes,
        extract_skills_from_text,
        extract_sections,
        compute_cv_score,
        compute_skill_gaps,
    )

    try:
        cv = CVUpload.objects.select_related("user__profile").get(pk=cv_upload_id)
        cv.status = CVUpload.Status.PROCESSING
        cv.save(update_fields=["status"])

        # Read file bytes
        with cv.file.open("rb") as f:
            file_bytes = f.read()

        filename = cv.original_filename
        if not validate_magic_bytes(file_bytes, filename):
            raise ValueError(f"Invalid file format for {filename}")

        # Extract text
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext == "pdf":
            text = extract_text_from_pdf(file_bytes)
        elif ext in ("docx", "doc"):
            text = extract_text_from_docx(file_bytes)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        if not text.strip():
            raise ValueError(
                f"Could not extract text from CV ({filename}). "
                "The file may be image-based (scanned) or contain no selectable text."
            )

        # Analyze
        skills_data = extract_skills_from_text(text)
        sections = extract_sections(text)
        scores = compute_cv_score(text, skills_data, sections)

        # Get target role from user profile
        target_role = None
        try:
            target_role = cv.user.profile.target_role or None
        except Exception:
            pass

        gaps = compute_skill_gaps(skills_data["all"], target_role)
        grade = CVAnalysis.compute_grade(scores["overall"])

        # Deep analysis via FastAPI service
        deep_analysis: dict = {}
        cv_text_for_analysis = text[:8000]
        if len(text) > 8000:
            logger.info(
                "CV text truncated from %d to 8000 chars for deep analysis (cv_id=%s)",
                len(text),
                cv_upload_id,
            )
        try:
            resp = requests.post(
                f"{FASTAPI_BASE_URL}/analyze-cv-deep",
                json={"cv_text": cv_text_for_analysis},
                timeout=30,
            )
            if resp.ok:
                deep_analysis = resp.json()
            else:
                logger.warning(
                    "Deep CV analysis returned non-OK status %s: %s",
                    resp.status_code,
                    resp.text,
                )
        except Exception as exc:
            logger.warning("Deep CV analysis call failed (non-fatal): %s", exc)

        # Save or update analysis
        CVAnalysis.objects.update_or_create(
            cv=cv,
            defaults={
                "overall_score": scores["overall"],
                "grade": grade,
                "keyword_relevance_score": scores["keyword_relevance"],
                "completeness_score": scores["completeness"],
                "skill_density_score": scores["skill_density"],
                "formatting_score": scores["formatting"],
                "extracted_skills": skills_data["all"],
                "skills_by_category": skills_data["by_category"],
                "skill_gaps": gaps,
                "raw_text": text[:5000],  # Store first 5000 chars only
                "deep_analysis": deep_analysis,
            },
        )

        cv.status = CVUpload.Status.COMPLETED
        cv.processed_at = timezone.now()
        cv.save(update_fields=["status", "processed_at"])

        logger.info("CV analysis completed for %s — Score: %s", cv_upload_id, scores["overall"])
        return {"cv_id": cv_upload_id, "score": scores["overall"]}

    except CVUpload.DoesNotExist:
        logger.error("CVUpload %s not found", cv_upload_id)
        raise
    except Exception as exc:
        logger.error("CV analysis failed for %s: %s", cv_upload_id, exc)
        try:
            cv = CVUpload.objects.get(pk=cv_upload_id)
            cv.status = CVUpload.Status.FAILED
            cv.error_message = str(exc)
            cv.save(update_fields=["status", "error_message"])
        except Exception:
            pass
        raise self.retry(exc=exc)
