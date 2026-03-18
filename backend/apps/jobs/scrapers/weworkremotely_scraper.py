"""
We Work Remotely job scraper — RSS feeds via feedparser.
"""
import time

import feedparser

from .base_scraper import BaseScraper

RSS_FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-data-science-jobs.rss",
]


class WeWorkRemotelyScraper(BaseScraper):
    """Scrapes remote jobs from We Work Remotely RSS feeds."""

    def __init__(self):
        super().__init__(source="weworkremotely")

    def fetch_jobs(self) -> int:
        total_found = 0

        for feed_url in RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_url)
            except Exception as exc:
                self.log_error(f"feedparser error for {feed_url}: {exc}")
                time.sleep(2)
                continue

            if getattr(feed, "bozo", False):
                bozo_exc = getattr(feed, "bozo_exception", None)
                self.logger.warning(
                    "Bozo feed (malformed) %s — %s", feed_url, bozo_exc
                )
                # Still attempt to parse entries if any were returned

            entries = getattr(feed, "entries", [])
            if not entries:
                self.logger.info("No entries in feed %s", feed_url)
                time.sleep(2)
                continue

            for entry in entries:
                url = (getattr(entry, "link", None) or "").strip()
                if not url:
                    continue

                if self.job_exists(url):
                    self._increment_run_counter(jobs_skipped=1)
                    continue

                # WWR title format: "CompanyName: Job Title"
                raw_title = getattr(entry, "title", "") or ""
                if ": " in raw_title:
                    company, title = raw_title.split(": ", 1)
                else:
                    company = ""
                    title = raw_title

                description = self._clean_html(
                    getattr(entry, "summary", "")
                    or getattr(entry, "description", "")
                )

                job_data = {
                    "title": title.strip(),
                    "company": company.strip(),
                    "location": "Worldwide",
                    "description": description,
                    "url": url,
                    "is_remote": True,
                    "job_type": "remote",
                    "source": "weworkremotely",
                }

                _, created = self.save_job(job_data)
                total_found += 1
                if created:
                    self._increment_run_counter(jobs_found=1, jobs_added=1)
                else:
                    self._increment_run_counter(jobs_found=1, jobs_updated=1)

            time.sleep(2)

        return total_found
