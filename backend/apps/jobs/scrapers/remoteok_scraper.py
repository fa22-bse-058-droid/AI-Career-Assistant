"""
Remote OK job scraper — JSON API with browser User-Agent.
"""
import time

from .base_scraper import BaseScraper

API_URL = "https://remoteok.com/api"
MAX_JOBS = 150

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class RemoteOkScraper(BaseScraper):
    """Scrapes remote jobs from Remote OK's public JSON API."""

    def __init__(self):
        super().__init__(source="remote_ok")

    def _get_headers(self) -> dict:
        headers = super()._get_headers()
        # Remote OK requires a real browser User-Agent
        headers["User-Agent"] = BROWSER_USER_AGENT
        return headers

    def fetch_jobs(self) -> int:
        total_found = 0

        response = self._make_request(API_URL)
        if response is None:
            self.log_error("Failed to fetch Remote OK API")
            return total_found

        try:
            jobs_raw = response.json()
        except Exception as exc:
            self.log_error(f"JSON parse error from Remote OK: {exc}")
            return total_found

        # First element is metadata (contains 'legal' key) — skip it
        jobs = jobs_raw[1:] if jobs_raw else []

        for job in jobs:
            if total_found >= MAX_JOBS:
                break

            # Filter to worldwide / empty / remote location only
            location = (job.get("location") or "").strip()
            if location and location.lower() not in ("", "worldwide", "remote"):
                if "remote" not in location.lower() and "worldwide" not in location.lower():
                    continue

            url = (job.get("url") or "").strip()
            if not url:
                continue

            if self.job_exists(url):
                self._increment_run_counter(jobs_skipped=1)
                continue

            description = self._clean_html(job.get("description", ""))
            tags = job.get("tags", [])
            if not isinstance(tags, list):
                tags = []

            job_data = {
                "title": job.get("position", ""),
                "company": job.get("company", ""),
                "location": location or "Worldwide",
                "description": description,
                "url": url,
                "is_remote": True,
                "salary_display": job.get("salary", ""),
                "job_type": "remote",
                "source": "remote_ok",
                "skills_required": tags,
            }

            _, created = self.save_job(job_data)
            total_found += 1
            if created:
                self._increment_run_counter(jobs_found=1, jobs_added=1)
            else:
                self._increment_run_counter(jobs_found=1, jobs_updated=1)

        # API is a single call — sleep after to be polite
        time.sleep(3)

        return total_found
