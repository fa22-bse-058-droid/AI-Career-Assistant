"""
Abstract base scraper for the Jobs app.
"""
import logging
import random
import time
from abc import ABC, abstractmethod
from datetime import timedelta

import requests
from bs4 import BeautifulSoup
from django.db.models import F
from django.utils import timezone
from fake_useragent import UserAgent


TECH_SKILLS = [
    "Python", "Django", "React", "Node.js", "TypeScript", "AWS", "Docker",
    "Kubernetes", "PostgreSQL", "MongoDB", "FastAPI", "Flask", "Vue.js",
    "Angular", "Flutter", "Kotlin", "Swift", "TensorFlow", "PyTorch",
    "scikit-learn", "Pandas", "NumPy", "Git", "Linux", "Java", "C++",
    "PHP", "Ruby", "Go", "Rust", "MySQL", "Redis", "GraphQL", "REST",
    "HTML", "CSS", "JavaScript", "Sass", "Tailwind", "Bootstrap",
    "Next.js", "Nuxt.js", "Express", "Spring", "Laravel", "Rails",
    "Celery", "RabbitMQ", "Kafka", "Elasticsearch", "Firebase",
    "Azure", "GCP", "Terraform", "Ansible", "Jenkins", "CI/CD",
]
# Build lowercase lookup set for fast matching
_SKILLS_LOWER = {s.lower(): s for s in TECH_SKILLS}

# Remote-first source identifiers
REMOTE_SOURCES = {"remotive", "weworkremotely", "arbeitnow", "remote_ok"}


class BaseScraper(ABC):
    """Abstract base class for all job scrapers."""

    def __init__(self, source: str):
        self.source = source
        self.session = requests.Session()
        self.ua = UserAgent()
        self.scraper_run = None
        self.logger = logging.getLogger(
            f"apps.jobs.scrapers.{source}"
        )
        self._last_status_code: int | None = None

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _get_headers(self) -> dict:
        return {
            "User-Agent": self.ua.random,
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "identity",
            "Referer": "https://www.google.com/",
            "Connection": "keep-alive",
        }

    def _make_request(
        self,
        url: str,
        params: dict | None = None,
        max_retries: int = 3,
    ) -> requests.Response | None:
        self._last_status_code = None

        for attempt in range(max_retries):
            # Sleep before every request (including first) as per spec
            time.sleep(random.uniform(1.5, 4.0))

            try:
                response = self.session.get(
                    url,
                    params=params,
                    headers=self._get_headers(),
                    timeout=20,
                )
                self._last_status_code = response.status_code

                if response.status_code == 429:
                    self.logger.warning("Rate limited (429) on %s — waiting 60 s", url)
                    time.sleep(60)
                    # One more attempt after rate-limit wait, counting as part of retries
                    continue

                if response.status_code == 403:
                    self.logger.warning("Access forbidden (403) for %s", url)
                    return None

                response.raise_for_status()
                return response
            except requests.exceptions.ConnectionError as exc:
                self.logger.warning(
                    "ConnectionError attempt %d/%d for %s: %s",
                    attempt + 1, max_retries, url, exc,
                )
            except requests.exceptions.Timeout as exc:
                self.logger.warning(
                    "Timeout attempt %d/%d for %s: %s",
                    attempt + 1, max_retries, url, exc,
                )
            except requests.exceptions.TooManyRedirects as exc:
                self.logger.warning("TooManyRedirects for %s: %s", url, exc)
                return None
            except requests.exceptions.HTTPError as exc:
                self.logger.warning("HTTPError for %s: %s", url, exc)
                return None

            # Exponential back-off before retry
            backoff = 2 ** attempt
            self.logger.debug("Backing off %d s before retry", backoff)
            time.sleep(backoff)

        self.logger.error("All %d retries exhausted for %s", max_retries, url)
        return None

    # ------------------------------------------------------------------
    # Skill / text helpers
    # ------------------------------------------------------------------

    def _extract_skills_from_text(self, text: str) -> list:
        if not text:
            return []
        text_lower = text.lower()
        found = []
        for skill_lower, skill_canonical in _SKILLS_LOWER.items():
            if skill_lower in text_lower:
                found.append(skill_canonical)
        return found

    def _clean_html(self, raw_html: str | None) -> str:
        if not raw_html:
            return ""
        try:
            soup = BeautifulSoup(raw_html, "html.parser")
            return soup.get_text(separator=" ", strip=True)
        except Exception:
            return raw_html or ""

    # ------------------------------------------------------------------
    # Scraper run lifecycle
    # ------------------------------------------------------------------

    def start_run(self, triggered_by: str = "scheduled"):
        from apps.jobs.models import ScraperRun

        self.scraper_run = ScraperRun.objects.create(
            source=self.source,
            triggered_by=triggered_by,
            status=ScraperRun.StatusChoice.RUNNING,
        )
        self.logger.info("ScraperRun %s started for source=%s", self.scraper_run.pk, self.source)
        return self.scraper_run

    def end_run(self, success: bool = True):
        if not self.scraper_run:
            return
        from apps.jobs.models import ScraperRun

        self.scraper_run.ended_at = timezone.now()
        if success:
            self.scraper_run.status = ScraperRun.StatusChoice.COMPLETED
        else:
            self.scraper_run.status = ScraperRun.StatusChoice.FAILED
        self.scraper_run.save()
        self.logger.info(
            "ScraperRun %s ended — status=%s found=%d added=%d",
            self.scraper_run.pk,
            self.scraper_run.status,
            self.scraper_run.jobs_found,
            self.scraper_run.jobs_added,
        )

    def log_error(self, msg: str):
        self.logger.error(msg)
        if self.scraper_run:
            errors = self.scraper_run.errors or []
            errors.append(msg)
            self.scraper_run.errors = errors
            self.scraper_run.save(update_fields=["errors"])

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------

    def job_exists(self, url: str) -> bool:
        from apps.jobs.models import JobListing

        return JobListing.objects.filter(url=url).exists()

    def save_job(self, data: dict):
        from apps.jobs.models import JobListing

        url = data.get("url", "").strip()
        if not url:
            return None, False

        # Auto-detect remote flag
        is_remote = (
            data.get("source", "") in REMOTE_SOURCES
            or "remote" in data.get("location", "").lower()
        )

        # Extract skills from combined text
        combined_text = (
            f"{data.get('title', '')} {data.get('description', '')} "
            f"{data.get('requirements', '')}"
        )
        skills = self._extract_skills_from_text(combined_text)

        expires_at = timezone.now() + timedelta(days=30)

        defaults = {
            "title": (data.get("title") or "Unknown")[:255],
            "company": (data.get("company") or "Unknown")[:255],
            "location": (data.get("location") or "")[:255],
            "job_type": data.get("job_type", JobListing.JobType.FULL_TIME),
            "experience_level": data.get(
                "experience_level", JobListing.ExperienceLevel.ANY
            ),
            "description": data.get("description") or "",
            "requirements": data.get("requirements") or "",
            "salary_min": data.get("salary_min"),
            "salary_max": data.get("salary_max"),
            "salary_display": (data.get("salary_display") or "")[:100],
            "source": data.get("source", self.source),
            "is_active": True,
            "is_remote": is_remote,
            "skills_required": skills,
            "raw_html": data.get("raw_html") or "",
            "expires_at": expires_at,
        }

        job, created = JobListing.objects.update_or_create(url=url, defaults=defaults)
        return job, created

    def _increment_run_counter(self, **fields):
        """Increment ScraperRun counters using F() expressions (one DB UPDATE)."""
        if not self.scraper_run:
            return
        update_kwargs = {field: F(field) + amount for field, amount in fields.items()}
        type(self.scraper_run).objects.filter(pk=self.scraper_run.pk).update(**update_kwargs)

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def fetch_jobs(self) -> int:
        """Fetch and save jobs. Return count of jobs found."""

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self, triggered_by: str = "scheduled"):
        self.start_run(triggered_by=triggered_by)
        try:
            self.fetch_jobs()
            self.end_run(success=True)
        except Exception as exc:
            self.log_error(f"Unhandled exception in {self.source} scraper: {exc}")
            self.end_run(success=False)
        # Refresh from DB so callers see accurate counters
        if self.scraper_run:
            self.scraper_run.refresh_from_db()
        return self.scraper_run
