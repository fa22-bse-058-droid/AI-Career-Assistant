"""
Abstract base scraper class for job listing scrapers.
"""
import logging
import random
import time
from abc import ABC, abstractmethod
from datetime import timedelta

import requests
from django.utils import timezone
from fake_useragent import UserAgent

SKILLS_KEYWORDS = [
    "python", "django", "flask", "fastapi",
    "javascript", "typescript", "react", "vue", "angular", "next.js",
    "node.js", "express",
    "java", "spring", "kotlin",
    "c", "c++", "c#", ".net",
    "php", "laravel",
    "ruby", "rails",
    "go", "golang",
    "rust",
    "swift", "ios", "android",
    "sql", "mysql", "postgresql", "mongodb", "redis", "sqlite",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
    "git", "github", "gitlab", "ci/cd", "devops",
    "html", "css", "tailwind", "bootstrap",
    "machine learning", "deep learning", "nlp", "tensorflow", "pytorch",
    "data analysis", "pandas", "numpy", "scikit-learn", "matplotlib",
    "rest api", "graphql", "microservices",
    "linux", "bash", "shell scripting",
    "agile", "scrum",
    "excel", "power bi", "tableau",
    "selenium", "testing", "pytest",
    "wordpress", "shopify",
    "figma", "photoshop",
    "oracle", "elasticsearch",
]


class BaseScraper(ABC):
    """Abstract base class for all job scrapers."""

    source: str = ""
    BASE_URL: str = ""

    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.scraper_run = None
        self.logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------ #
    # HTTP helpers
    # ------------------------------------------------------------------ #

    def _get_headers(self) -> dict:
        return {
            "User-Agent": self.ua.random,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": self.BASE_URL,
        }

    def _make_request(self, url: str, params=None, max_retries: int = 3):
        """Make an HTTP GET request with retries and rate-limiting."""
        for attempt in range(max_retries):
            # Rate-limit: random sleep before every request
            time.sleep(random.uniform(1.5, 4.0))
            try:
                self.logger.info("Requesting URL (attempt %d): %s", attempt + 1, url)
                resp = self.session.get(
                    url,
                    params=params,
                    headers=self._get_headers(),
                    timeout=15,
                )
                self.logger.info("Response status %d for %s", resp.status_code, url)

                if resp.status_code == 403:
                    self.logger.warning("403 Forbidden for %s — aborting", url)
                    return None

                if resp.status_code == 429:
                    self.logger.warning("429 Too Many Requests — waiting 60 s")
                    time.sleep(60)
                    continue

                resp.raise_for_status()
                return resp

            except requests.exceptions.ConnectionError as exc:
                self.logger.warning("ConnectionError on %s (attempt %d): %s", url, attempt + 1, exc)
            except requests.exceptions.Timeout as exc:
                self.logger.warning("Timeout on %s (attempt %d): %s", url, attempt + 1, exc)
            except requests.exceptions.TooManyRedirects as exc:
                self.logger.warning("TooManyRedirects on %s: %s", url, exc)
                return None
            except requests.exceptions.HTTPError as exc:
                self.logger.warning("HTTPError on %s (attempt %d): %s", url, attempt + 1, exc)

            # Exponential backoff
            time.sleep(2 ** attempt)

        self.logger.error("All %d attempts failed for %s", max_retries, url)
        return None

    # ------------------------------------------------------------------ #
    # Skill extraction
    # ------------------------------------------------------------------ #

    def _extract_skills_from_text(self, text: str) -> list:
        if not text:
            return []
        text_lower = text.lower()
        found = [skill for skill in SKILLS_KEYWORDS if skill in text_lower]
        return list(dict.fromkeys(found))  # deduplicate, preserve order

    # ------------------------------------------------------------------ #
    # ScraperRun lifecycle
    # ------------------------------------------------------------------ #

    def start_run(self):
        from apps.jobs.models import ScraperRun
        self.scraper_run = ScraperRun.objects.create(
            source=self.source,
            status=ScraperRun.Status.RUNNING,
        )
        return self.scraper_run

    def end_run(self, success: bool = True):
        if not self.scraper_run:
            return
        from apps.jobs.models import ScraperRun
        self.scraper_run.ended_at = timezone.now()
        self.scraper_run.status = (
            ScraperRun.Status.COMPLETED if success else ScraperRun.Status.FAILED
        )
        self.scraper_run.save()

    def log_error(self, error_msg: str):
        self.logger.error(error_msg)
        if self.scraper_run:
            errors = list(self.scraper_run.errors or [])
            errors.append(error_msg)
            self.scraper_run.errors = errors
            self.scraper_run.save(update_fields=["errors"])

    # ------------------------------------------------------------------ #
    # Job persistence
    # ------------------------------------------------------------------ #

    def job_exists(self, url: str) -> bool:
        from apps.jobs.models import JobListing
        return JobListing.objects.filter(url=url).exists()

    def save_job(self, data: dict):
        """Persist a job dict. Returns (instance, created)."""
        from apps.jobs.models import JobListing

        url = data.get("url", "").strip()
        if not url:
            return None, False

        # Extract skills from description before saving
        combined_text = f"{data.get('description', '')} {data.get('requirements', '')}"
        extracted_skills = self._extract_skills_from_text(combined_text)

        now = timezone.now()
        defaults = {
            "title": (data.get("title") or "Unknown")[:255],
            "company": (data.get("company") or "Unknown")[:255],
            "location": (data.get("location") or "")[:255],
            "job_type": data.get("job_type", JobListing.JobType.FULL_TIME),
            "experience_level": data.get("experience_level", JobListing.ExperienceLevel.ANY),
            "description": data.get("description", ""),
            "requirements": data.get("requirements", ""),
            "salary_min": data.get("salary_min"),
            "salary_max": data.get("salary_max"),
            "salary_display": (data.get("salary_display") or "")[:100],
            "source": data.get("source", self.source),
            "skills_required": extracted_skills,
            "raw_html": data.get("raw_html", ""),
            "is_active": True,
        }

        existing = JobListing.objects.filter(url=url).first()
        if existing:
            # Update mutable fields if they changed
            updated = False
            for field in ("description", "requirements", "salary_min", "salary_max", "salary_display"):
                new_val = defaults.get(field)
                if new_val and getattr(existing, field) != new_val:
                    setattr(existing, field, new_val)
                    updated = True
            if updated:
                existing.save()
            return existing, False

        instance = JobListing.objects.create(url=url, expires_at=now + timedelta(days=30), **defaults)
        return instance, True

    # ------------------------------------------------------------------ #
    # Abstract interface
    # ------------------------------------------------------------------ #

    @abstractmethod
    def fetch_jobs(self) -> int:
        """Fetch and save jobs. Returns count of jobs added."""
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    # Main entry point
    # ------------------------------------------------------------------ #

    def run(self):
        """Orchestrates start_run → fetch_jobs → end_run. Never crashes."""
        self.start_run()
        try:
            self.fetch_jobs()
            self.end_run(success=True)
        except Exception as exc:
            self.log_error(f"Unhandled error in scraper run: {exc}")
            self.end_run(success=False)
        return self.scraper_run
