"""
Celery tasks for job scraping, matching, and maintenance.
"""
import logging
from functools import lru_cache

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_sentence_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


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


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    name="apps.jobs.tasks.scrape_remotive",
)
def scrape_remotive(self, triggered_by="scheduled"):
    from .scrapers import RemotiveScraper

    scraper = RemotiveScraper()
    try:
        run = scraper.run(triggered_by=triggered_by)
        logger.info(
            "Remotive scrape done: found=%d added=%d",
            run.jobs_found,
            run.jobs_added,
        )
        return {"source": "remotive", "jobs_added": run.jobs_added}
    except Exception as exc:
        logger.error("Remotive scrape task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    name="apps.jobs.tasks.scrape_weworkremotely",
)
def scrape_weworkremotely(self, triggered_by="scheduled"):
    from .scrapers import WeWorkRemotelyScraper

    scraper = WeWorkRemotelyScraper()
    try:
        run = scraper.run(triggered_by=triggered_by)
        logger.info(
            "WeWorkRemotely scrape done: found=%d added=%d",
            run.jobs_found,
            run.jobs_added,
        )
        return {"source": "weworkremotely", "jobs_added": run.jobs_added}
    except Exception as exc:
        logger.error("WeWorkRemotely scrape task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    name="apps.jobs.tasks.scrape_arbeitnow",
)
def scrape_arbeitnow(self, triggered_by="scheduled"):
    from .scrapers import ArbeitnowScraper

    scraper = ArbeitnowScraper()
    try:
        run = scraper.run(triggered_by=triggered_by)
        logger.info(
            "Arbeitnow scrape done: found=%d added=%d",
            run.jobs_found,
            run.jobs_added,
        )
        return {"source": "arbeitnow", "jobs_added": run.jobs_added}
    except Exception as exc:
        logger.error("Arbeitnow scrape task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    name="apps.jobs.tasks.scrape_remoteok",
)
def scrape_remoteok(self, triggered_by="scheduled"):
    from .scrapers import RemoteOkScraper

    scraper = RemoteOkScraper()
    try:
        run = scraper.run(triggered_by=triggered_by)
        logger.info(
            "RemoteOk scrape done: found=%d added=%d",
            run.jobs_found,
            run.jobs_added,
        )
        return {"source": "remote_ok", "jobs_added": run.jobs_added}
    except Exception as exc:
        logger.error("RemoteOk scrape task failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(name="apps.jobs.tasks.scrape_remote_sources")
def scrape_remote_sources(triggered_by="scheduled"):
    """Dispatch all remote-platform scrapers."""
    scrape_remotive.delay(triggered_by=triggered_by)
    scrape_weworkremotely.delay(triggered_by=triggered_by)
    scrape_arbeitnow.delay(triggered_by=triggered_by)
    scrape_remoteok.delay(triggered_by=triggered_by)


@shared_task(name="apps.jobs.tasks.scrape_all_sources")
def scrape_all_sources(triggered_by="scheduled"):
    scrape_rozee.delay(triggered_by=triggered_by)
    scrape_indeed.delay(triggered_by=triggered_by)
    scrape_linkedin.delay(triggered_by=triggered_by)
    scrape_remote_sources.delay(triggered_by=triggered_by)


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


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    name="apps.jobs.tasks.compute_matches_for_user",
)
def compute_matches_for_user(self, user_id: str):
    """
    Batch-compute semantic job matches for a single user using the MiniLM
    model via apps.jobs.utils.matcher.batch_compute_matches().
    """
    from apps.authentication.models import CustomUser
    from apps.cv_analyzer.models import CVUpload
    from apps.jobs.models import JobListing, UserJobMatch
    from apps.jobs.utils.matcher import batch_compute_matches

    try:
        user = CustomUser.objects.get(pk=user_id)
        latest_cv = (
            CVUpload.objects.filter(user=user, status="completed")
            .order_by("-uploaded_at")
            .first()
        )
        if not latest_cv:
            logger.info("No completed CV for user %s — skipping match", user_id)
            return

        analysis = getattr(latest_cv, "analysis", None)
        cv_text = getattr(analysis, "raw_text", "") or ""
        cv_skills = getattr(analysis, "extracted_skills", None) or []

        if not cv_text:
            logger.info("Empty CV text for user %s — skipping match", user_id)
            return

        active_jobs = JobListing.objects.filter(is_active=True)

        matches = batch_compute_matches(
            cv_text=cv_text,
            jobs_queryset=active_jobs,
            cv_skills=cv_skills,
        )

        for match in matches:
            UserJobMatch.objects.update_or_create(
                user=user,
                job_id=match["job_id"],
                defaults={
                    "score": round(match["score"], 4),
                    "skill_overlap": match["skill_overlap"],
                    "skill_overlap_count": match["skill_overlap_count"],
                },
            )

        logger.info(
            "Computed %d job matches for user %s", len(matches), user_id
        )
    except Exception as exc:
        logger.error("compute_matches_for_user failed for %s: %s", user_id, exc)
        raise self.retry(exc=exc)


@shared_task(name="apps.jobs.tasks.recompute_all_matches")
def recompute_all_matches():
    """Recompute job matches for all users who have a completed CVAnalysis."""
    from apps.authentication.models import CustomUser
    from apps.cv_analyzer.models import CVAnalysis

    user_ids = (
        CVAnalysis.objects.filter(cv__status="completed")
        .values_list("cv__user_id", flat=True)
        .distinct()
    )

    dispatched = 0
    for user_id in user_ids:
        compute_matches_for_user.delay(str(user_id))
        dispatched += 1

    logger.info("recompute_all_matches: dispatched %d user match tasks", dispatched)
    return dispatched
