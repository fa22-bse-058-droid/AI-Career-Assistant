"""
Remotive.com job scraper — JSON API.
"""
import time

from .base_scraper import BaseScraper

API_URL = "https://remotive.com/api/remote-jobs"

CATEGORIES = [
    "software-dev",
    "devops-sysadmin",
    "data",
    "product",
    "backend",
    "frontend",
]

MAX_JOBS = 200


class RemotiveScraper(BaseScraper):
    """Scrapes remote jobs from Remotive's public JSON API."""

    def __init__(self):
        super().__init__(source="remotive")

    def fetch_jobs(self) -> int:
        total_found = 0

        for category in CATEGORIES:
            if total_found >= MAX_JOBS:
                break

            response = self._make_request(
                API_URL,
                params={"category": category, "limit": 100},
            )
            if response is None:
                self.log_error(f"Failed to fetch remotive category '{category}'")
                time.sleep(1)
                continue

            try:
                data = response.json()
            except Exception as exc:
                self.log_error(f"JSON parse error for category '{category}': {exc}")
                time.sleep(1)
                continue

            jobs = data.get("jobs", [])
            for job in jobs:
                if total_found >= MAX_JOBS:
                    break

                url = (job.get("url") or "").strip()
                if not url:
                    continue

                if self.job_exists(url):
                    self._increment_run_counter(jobs_skipped=1)
                    continue

                description = self._clean_html(job.get("description", ""))

                job_data = {
                    "title": job.get("title", ""),
                    "company": job.get("company_name", ""),
                    "location": job.get("candidate_required_location") or "Worldwide",
                    "description": description,
                    "url": url,
                    "salary_display": job.get("salary", ""),
                    "is_remote": True,
                    "job_type": "remote",
                    "source": "remotive",
                }

                _, created = self.save_job(job_data)
                total_found += 1
                if created:
                    self._increment_run_counter(jobs_found=1, jobs_added=1)
                else:
                    self._increment_run_counter(jobs_found=1, jobs_updated=1)

            time.sleep(1)

        return total_found
