"""
Celery tasks for job scraping, matching, and maintenance.
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, name="jobs.scrape_rozee")
def scrape_rozee(self):
    """Scrape Rozee.pk and return the ScraperRun id."""
    try:
        from .scrapers import RozeeScraper
        scraper = RozeeScraper()
        run = scraper.run()
        logger.info(
            "Rozee scrape done: %d found, %d added",
            run.jobs_found, run.jobs_added,
        )
        return str(run.id)
    except Exception as exc:
        logger.error("scrape_rozee failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3, name="jobs.scrape_indeed")
def scrape_indeed(self):
    """Scrape Indeed PK and return the ScraperRun id."""
    try:
        from .scrapers import IndeedScraper
        scraper = IndeedScraper()
        run = scraper.run()
        logger.info(
            "Indeed scrape done: %d found, %d added",
            run.jobs_found, run.jobs_added,
        )
        return str(run.id)
    except Exception as exc:
        logger.error("scrape_indeed failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3, name="jobs.scrape_all_sources")
def scrape_all_sources(self):
    """Trigger both scrapers and schedule match recomputation afterwards."""
    logger.info("Triggering all job scrapers")
    scrape_rozee.delay()
    scrape_indeed.delay()
    recompute_all_matches.delay()
    return {"triggered": ["rozee", "indeed"]}


@shared_task(bind=True, max_retries=3, name="jobs.purge_expired_listings")
def purge_expired_listings(self):
    """Mark expired jobs inactive and remove their match records."""
    from .models import JobListing, UserJobMatch
    now = timezone.now()
    expired_qs = JobListing.objects.filter(expires_at__lt=now, is_active=True)
    expired_ids = list(expired_qs.values_list("id", flat=True))
    count = expired_qs.update(is_active=False)
    if expired_ids:
        UserJobMatch.objects.filter(job_id__in=expired_ids).delete()
    logger.info("Purged %d expired job listings", count)
    return count


# Keep old name as alias so existing beat schedule entry still resolves
purge_expired_jobs = purge_expired_listings


_MATCH_CHUNK_SIZE = 100  # jobs per chunk when computing matches


@shared_task(bind=True, max_retries=3, name="jobs.compute_matches_for_user")
def compute_matches_for_user(self, user_id: str):
    """Compute cosine-similarity match scores for a single user."""
    from .models import JobListing, UserJobMatch
    from apps.authentication.models import CustomUser
    from apps.cv_analyzer.models import CVUpload

    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        logger.warning("compute_matches_for_user: user %s not found", user_id)
        return 0

    # Get latest completed CV upload
    latest_cv = (
        CVUpload.objects.filter(user=user, status="completed")
        .order_by("-uploaded_at")
        .first()
    )
    if not latest_cv:
        logger.info("compute_matches_for_user: no completed CV for user %s", user_id)
        return 0

    try:
        analysis = latest_cv.analysis
        cv_skills = list(analysis.extracted_skills or [])
        cv_text = analysis.raw_text or " ".join(cv_skills)
    except Exception:
        logger.warning("compute_matches_for_user: no CVAnalysis for user %s", user_id)
        return 0

    if not cv_text:
        return 0

    from .utils.matcher import batch_compute_matches

    active_jobs = JobListing.objects.filter(is_active=True)
    count = 0

    job_ids = list(active_jobs.values_list("id", flat=True))
    for i in range(0, len(job_ids), _MATCH_CHUNK_SIZE):
        chunk_ids = job_ids[i : i + _MATCH_CHUNK_SIZE]
        chunk_qs = JobListing.objects.filter(id__in=chunk_ids)
        matches = batch_compute_matches(cv_text, chunk_qs, cv_skills)

        for m in matches:
            UserJobMatch.objects.update_or_create(
                user=user,
                job_id=m["job_id"],
                defaults={
                    "score": m["score"],
                    "skill_overlap": m["skill_overlap"],
                    "skill_overlap_count": m["skill_overlap_count"],
                },
            )
            count += 1

    logger.info("Computed %d matches for user %s", count, user_id)
    return count


@shared_task(bind=True, max_retries=3, name="jobs.recompute_all_matches")
def recompute_all_matches(self):
    """Re-trigger match computation for every user who has a completed CVAnalysis."""
    from apps.cv_analyzer.models import CVAnalysis
    user_ids = (
        CVAnalysis.objects.select_related("cv__user")
        .values_list("cv__user_id", flat=True)
        .distinct()
    )
    count = 0
    for uid in user_ids:
        compute_matches_for_user.delay(str(uid))
        count += 1
    logger.info("Queued match recomputation for %d users", count)
    return count
