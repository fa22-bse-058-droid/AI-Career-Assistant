"""
LinkedIn job scraper using the public RSS/Atom feed.
"""
import random
import time

from .base_scraper import BaseScraper


SEARCH_QUERIES = [
    "software engineer Pakistan",
    "python developer Pakistan",
    "web developer Pakistan",
    "react developer Pakistan",
    "django developer Pakistan",
    "frontend developer Pakistan",
    "backend developer Pakistan",
    "full stack developer Pakistan",
    "data analyst Pakistan",
    "software internship Pakistan",
    "it internship Pakistan",
    "fresh graduate it Pakistan",
]

RSS_URL = (
    "https://www.linkedin.com/jobs/search/"
    "?keywords={query}&location=Pakistan&f_TPR=r604800"
)

MAX_JOBS = 50


class LinkedInScraper(BaseScraper):

    def __init__(self):
        super().__init__(source="linkedin")

    def fetch_jobs(self) -> int:
        import feedparser  # imported at function level as per spec

        total_found = 0

        for query in SEARCH_QUERIES:
            if total_found >= MAX_JOBS:
                break

            url = RSS_URL.format(query=query.replace(" ", "+"))

            try:
                feed = feedparser.parse(url)
            except Exception as exc:
                self.log_error(f"feedparser failed for query '{query}': {exc}")
                time.sleep(random.uniform(2.0, 3.0))
                continue

            # bozo=True means the feed is malformed — log and skip but don't error
            if feed.get("bozo"):
                self.logger.warning(
                    "LinkedIn feed for '%s' is malformed (bozo=True), skipping",
                    query,
                )
                time.sleep(random.uniform(2.0, 3.0))
                continue

            entries = feed.get("entries", [])

            # 0 results is NORMAL for LinkedIn RSS — not an error
            if not entries:
                self.logger.info(
                    "LinkedIn RSS returned 0 results for '%s' (normal)", query
                )
                time.sleep(random.uniform(2.0, 3.0))
                continue

            for entry in entries:
                if total_found >= MAX_JOBS:
                    break

                job_data = self._parse_entry(entry)
                if not job_data:
                    continue

                job_url = job_data.get("url", "")
                if self.job_exists(job_url):
                    self._increment_run_counter(jobs_skipped=1)
                    continue

                _, created = self.save_job(job_data)
                total_found += 1
                if created:
                    self._increment_run_counter(jobs_found=1, jobs_added=1)
                else:
                    self._increment_run_counter(jobs_found=1, jobs_updated=1)

            # Polite delay between queries
            time.sleep(random.uniform(2.0, 3.0))

        return total_found

    def _parse_entry(self, entry) -> dict | None:
        try:
            title = (entry.get("title") or "").strip()
            url = (entry.get("link") or "").strip()

            if not title or not url:
                return None

            # Company and location are often in the summary
            summary_raw = entry.get("summary") or ""
            description = self._clean_html(summary_raw)

            # Try to get company/location from feed metadata
            company = (
                entry.get("author")
                or entry.get("company")
                or "Unknown"
            ).strip()
            location = (entry.get("location") or "Pakistan").strip()

            job_type = self._detect_job_type(title, description)

            return {
                "title": title[:255],
                "company": company[:255],
                "location": location[:255],
                "url": url,
                "source": "linkedin",
                "description": description,
                "requirements": "",
                "job_type": job_type,
            }
        except Exception as exc:
            self.logger.debug("_parse_entry error: %s", exc)
            return None

    def _detect_job_type(self, title: str, desc: str) -> str:
        combined = f"{title} {desc}".lower()
        if "intern" in combined or "internship" in combined:
            return "internship"
        if "remote" in combined:
            return "remote"
        if "hybrid" in combined:
            return "hybrid"
        if "part-time" in combined or "part time" in combined:
            return "part_time"
        return "full_time"
