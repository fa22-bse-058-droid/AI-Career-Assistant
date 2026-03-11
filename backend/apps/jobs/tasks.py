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
    name="jobs.scrape_rozee",
)
def scrape_rozee(self):
    from .scraper import RozeeScraper, save_jobs
    from .models import ScraperLog
    log = ScraperLog.objects.create(source="rozee", status="running")
    try:
        scraper = RozeeScraper()
        jobs = scraper.scrape()
        found, added = save_jobs(jobs)
        log.status = "success"
        log.jobs_found = found
        log.jobs_added = added
        log.finished_at = timezone.now()
        log.save()
        logger.info("Rozee scrape done: %d found, %d added", found, added)
    except Exception as exc:
        log.status = "failed"
        log.error_message = str(exc)
        log.finished_at = timezone.now()
        log.save()
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    name="jobs.scrape_indeed",
)
def scrape_indeed(self):
    from .scraper import IndeedScraper, save_jobs
    from .models import ScraperLog
    log = ScraperLog.objects.create(source="indeed", status="running")
    try:
        scraper = IndeedScraper()
        jobs = scraper.scrape()
        found, added = save_jobs(jobs)
        log.status = "success"
        log.jobs_found = found
        log.jobs_added = added
        log.finished_at = timezone.now()
        log.save()
        logger.info("Indeed scrape done: %d found, %d added", found, added)
    except Exception as exc:
        log.status = "failed"
        log.error_message = str(exc)
        log.finished_at = timezone.now()
        log.save()
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    name="jobs.scrape_linkedin",
)
def scrape_linkedin(self):
    from .scraper import LinkedInScraper, save_jobs
    from .models import ScraperLog
    log = ScraperLog.objects.create(source="linkedin", status="running")
    try:
        scraper = LinkedInScraper()
        jobs = scraper.scrape()
        found, added = save_jobs(jobs)
        log.status = "success"
        log.jobs_found = found
        log.jobs_added = added
        log.finished_at = timezone.now()
        log.save()
        logger.info("LinkedIn scrape done: %d found, %d added", found, added)
    except Exception as exc:
        log.status = "failed"
        log.error_message = str(exc)
        log.finished_at = timezone.now()
        log.save()
        raise self.retry(exc=exc)


@shared_task(name="jobs.scrape_all_sources")
def scrape_all_sources():
    scrape_rozee.delay()
    scrape_indeed.delay()
    scrape_linkedin.delay()


@shared_task(name="jobs.purge_expired_jobs")
def purge_expired_jobs():
    from .models import JobListing
    cutoff = timezone.now()
    deleted, _ = JobListing.objects.filter(expires_at__lt=cutoff).delete()
    logger.info("Purged %d expired jobs", deleted)
    return deleted


@shared_task(name="jobs.compute_job_matches_for_user")
def compute_job_matches_for_user(user_id: str):
    """Compute MiniLM-based job matches for a user against active listings."""
    from .models import JobListing, JobMatch
    from apps.authentication.models import CustomUser
    from apps.cv_analyzer.models import CVAnalysis, CVUpload
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
        user_skills = " ".join(analysis.extracted_skills)
        if not user_skills:
            return

        jobs = JobListing.objects.filter(is_active=True).values(
            "id", "title", "description", "skills_required"
        )

        # Use lazy-loaded singleton model
        model = _get_sentence_model()
        if model is None:
            logger.error("Sentence model not available for job matching")
            return
        from sentence_transformers import util

        user_embedding = model.encode(user_skills, convert_to_tensor=True)

        semantic_weight = settings.JOB_MATCH_SEMANTIC_WEIGHT
        keyword_weight = settings.JOB_MATCH_KEYWORD_WEIGHT
        threshold = settings.JOB_MATCH_THRESHOLD

        user_skills_lower = {s.lower() for s in analysis.extracted_skills}

        for job_data in jobs:
            job_text = f"{job_data['title']} {job_data['description']}"
            job_embedding = model.encode(job_text, convert_to_tensor=True)
            semantic_score = float(util.cos_sim(user_embedding, job_embedding)[0][0])

            job_skills = [s.lower() for s in (job_data["skills_required"] or [])]
            if job_skills:
                keyword_score = len(user_skills_lower & set(job_skills)) / len(job_skills)
            else:
                keyword_score = 0.5

            match_score = semantic_weight * semantic_score + keyword_weight * keyword_score

            if match_score >= threshold:
                JobMatch.objects.update_or_create(
                    user=user,
                    job_id=job_data["id"],
                    defaults={
                        "match_score": round(match_score, 4),
                        "semantic_score": round(semantic_score, 4),
                        "keyword_score": round(keyword_score, 4),
                    },
                )

        logger.info("Job matches computed for user %s", user_id)
    except Exception as exc:
        logger.error("Job matching failed for user %s: %s", user_id, exc)
        raise
