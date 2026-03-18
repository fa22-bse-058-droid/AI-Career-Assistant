"""
Arbeitnow job board scraper — paginated JSON API.
"""
import time

from .base_scraper import BaseScraper

API_URL = "https://www.arbeitnow.com/api/job-board-api"
MAX_PAGES = 5


class ArbeitnowScraper(BaseScraper):
    """Scrapes remote jobs from Arbeitnow's public job board API."""

    def __init__(self):
        super().__init__(source="arbeitnow")

    def fetch_jobs(self) -> int:
        total_found = 0

        for page in range(1, MAX_PAGES + 1):
            response = self._make_request(API_URL, params={"page": page})
            if response is None:
                self.log_error(f"Failed to fetch arbeitnow page {page}")
                time.sleep(1)
                continue

            try:
                data = response.json()
            except Exception as exc:
                self.log_error(f"JSON parse error on page {page}: {exc}")
                time.sleep(1)
                continue

            jobs = data.get("data", [])
            if not jobs:
                self.logger.info("No more jobs at page %d — stopping", page)
                break

            for job in jobs:
                is_remote = job.get("remote", False)
                location = job.get("location", "")

                # Filter: only include remote jobs or worldwide/remote locations
                if not (
                    is_remote
                    or "worldwide" in location.lower()
                    or "remote" in location.lower()
                ):
                    continue

                url = (job.get("url") or "").strip()
                if not url:
                    continue

                if self.job_exists(url):
                    self._increment_run_counter(jobs_skipped=1)
                    continue

                description = self._clean_html(job.get("description", ""))
                tags = job.get("tags", []) or []
                skills = list(tags) + self._extract_skills_from_text(description)

                job_data = {
                    "title": job.get("title", ""),
                    "company": job.get("company_name", ""),
                    "location": location or "Worldwide",
                    "description": description,
                    "url": url,
                    "is_remote": bool(is_remote),
                    "job_type": "remote" if is_remote else "full_time",
                    "source": "arbeitnow",
                    "skills_required": skills,
                }

                _, created = self.save_job(job_data)
                total_found += 1
                if created:
                    self._increment_run_counter(jobs_found=1, jobs_added=1)
                else:
                    self._increment_run_counter(jobs_found=1, jobs_updated=1)

            time.sleep(1)

        return total_found
