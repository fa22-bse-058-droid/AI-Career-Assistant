"""
Celery tasks for job scraping, matching, and maintenance.
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)

# Lazy singleton — load MiniLM once per worker process
_sentence_model = None


def _get_sentence_model():
    global _sentence_model
    if _sentence_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            logger.error("Failed to load SentenceTransformer: %s", e)
    return _sentence_model


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    name="apps.jobs.tasks.scrape_rozee",
)
def scrape_rozee(self, triggered_by="scheduled"):
    from .scrapers import RozeeScraper
    scraper = RozeeScraper()
    try:
        run = scraper.run(triggered_by=triggered_by)
        logger.info(
            "Rozee scrape done: found=%d added=%d",
            run.jobs_found,
            run.jobs_added,
        )
        return {"source": "rozee", "jobs_added": run.jobs_added}
    except Exception as exc:
        logger.error("Rozee scrape task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    name="apps.jobs.tasks.scrape_indeed",
)
def scrape_indeed(self, triggered_by="scheduled"):
    from .scrapers import IndeedScraper
    scraper = IndeedScraper()
    try:
        run = scraper.run(triggered_by=triggered_by)
        logger.info(
            "Indeed scrape done: found=%d added=%d",
            run.jobs_found,
            run.jobs_added,
        )
        return {"source": "indeed", "jobs_added": run.jobs_added}
    except Exception as exc:
        logger.error("Indeed scrape task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    name="apps.jobs.tasks.scrape_linkedin",
)
def scrape_linkedin(self, triggered_by="scheduled"):
    from .scrapers import LinkedInScraper
    scraper = LinkedInScraper()
    try:
        run = scraper.run(triggered_by=triggered_by)
        logger.info(
            "LinkedIn scrape done: found=%d added=%d",
            run.jobs_found,
            run.jobs_added,
        )
        return {"source": "linkedin", "jobs_added": run.jobs_added}
    except Exception as exc:
        logger.error("LinkedIn scrape task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(name="apps.jobs.tasks.scrape_all_sources")
def scrape_all_sources(triggered_by="scheduled"):
    scrape_rozee.delay(triggered_by=triggered_by)
    scrape_indeed.delay(triggered_by=triggered_by)
    scrape_linkedin.delay(triggered_by=triggered_by)


@shared_task(name="apps.jobs.tasks.purge_expired_jobs")
def purge_expired_jobs():
    from .models import JobListing
    cutoff = timezone.now()
    deleted, _ = JobListing.objects.filter(expires_at__lt=cutoff).delete()
    logger.info("Purged %d expired jobs", deleted)
    return deleted


@shared_task(name="apps.jobs.tasks.compute_job_matches_for_user")
def compute_job_matches_for_user(user_id: str):
    """Compute skill-based job matches for a user against active listings."""
    from .models import JobListing, UserJobMatch
    from apps.authentication.models import CustomUser
    from apps.cv_analyzer.models import CVUpload
    from django.conf import settings

    try:
        user = CustomUser.objects.get(pk=user_id)
        latest_cv = (
            CVUpload.objects.filter(user=user, status="completed")
            .order_by("-uploaded_at")
            .first()
        )
        if not latest_cv:
            return

        analysis = latest_cv.analysis
        user_skills_raw = getattr(analysis, "extracted_skills", None) or []
        if not user_skills_raw:
            return

        user_skills_lower = {s.lower() for s in user_skills_raw}

        jobs = JobListing.objects.filter(is_active=True).values(
            "id", "title", "description", "skills_required"
        )

        # Use lazy-loaded singleton model
        model = _get_sentence_model()
        if model is None:
            logger.error("Sentence model not available for job matching")
            return
        from sentence_transformers import util

        user_text = " ".join(user_skills_raw)
        user_embedding = model.encode(user_text, convert_to_tensor=True)

        semantic_weight = settings.JOB_MATCH_SEMANTIC_WEIGHT
        keyword_weight = settings.JOB_MATCH_KEYWORD_WEIGHT
        threshold = settings.JOB_MATCH_THRESHOLD

        for job_data in jobs:
            job_text = f"{job_data['title']} {job_data['description']}"
            job_embedding = model.encode(job_text, convert_to_tensor=True)
            semantic_score = float(util.cos_sim(user_embedding, job_embedding)[0][0])

            job_skills = [s.lower() for s in (job_data["skills_required"] or [])]
            if job_skills:
                overlap = list(user_skills_lower & set(job_skills))
                keyword_score = len(overlap) / len(job_skills)
            else:
                overlap = []
                keyword_score = 0.5

            score = semantic_weight * semantic_score + keyword_weight * keyword_score

            if score >= threshold:
                UserJobMatch.objects.update_or_create(
                    user=user,
                    job_id=job_data["id"],
                    defaults={
                        "score": round(score, 4),
                        "skill_overlap": overlap,
                        "skill_overlap_count": len(overlap),
                    },
                )

        logger.info("Job matches computed for user %s", user_id)
    except Exception as exc:
        logger.error("Job matching failed for user %s: %s", user_id, exc)
        raise
