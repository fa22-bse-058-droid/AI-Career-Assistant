"""
Rozee.pk job scraper.
"""
import time
import random

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper


SEARCH_QUERIES = [
    "software engineer",
    "python developer",
    "web developer",
    "react developer",
    "django developer",
    "frontend developer",
    "backend developer",
    "full stack developer",
    "data analyst",
    "software internship",
    "it internship",
    "fresh graduate it",
]


class RozeeScraper(BaseScraper):
    BASE_URL = "https://www.rozee.pk"

    def __init__(self):
        super().__init__(source="rozee")

    def fetch_jobs(self) -> int:
        total_found = 0

        for query in SEARCH_QUERIES:
            for page in range(1, 4):  # 3 pages per query
                url = f"{self.BASE_URL}/job/jsearch/q/{query.replace(' ', '+')}"
                params = {"fpn": page}
                response = self._make_request(url, params=params)
                if response is None:
                    self.log_error(f"Failed to fetch rozee page {page} for query '{query}'")
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                cards = soup.select(".job-listing, .job-item, [data-job-id]")
                if not cards:
                    break  # No more results for this query

                for card in cards:
                    job_data = self._parse_job_card(card)
                    if not job_data:
                        continue

                    job_url = job_data.get("url", "")
                    if self.job_exists(job_url):
                        self._increment_run_counter(jobs_skipped=1)
                        continue

                    # Fetch detail page for description (throttled)
                    detail = self._parse_job_detail(job_url)
                    job_data.update(detail)

                    _, created = self.save_job(job_data)
                    total_found += 1
                    if created:
                        self._increment_run_counter(jobs_found=1, jobs_added=1)
                    else:
                        self._increment_run_counter(jobs_found=1, jobs_updated=1)

        return total_found

    def _parse_job_card(self, card) -> dict | None:
        try:
            title_el = card.select_one(".job-title, h2 a, .title a")
            company_el = card.select_one(".company-name, .company a")
            location_el = card.select_one(".location, .loc")
            url_el = card.select_one("a[href]")

            if not title_el or not url_el:
                return None

            url = url_el.get("href", "")
            if not url:
                return None
            if not url.startswith("http"):
                url = self.BASE_URL + url

            return {
                "title": title_el.get_text(strip=True),
                "company": company_el.get_text(strip=True) if company_el else "Unknown",
                "location": location_el.get_text(strip=True) if location_el else "",
                "url": url,
                "source": "rozee",
                "description": "",
                "requirements": "",
            }
        except Exception as exc:
            self.logger.debug("_parse_job_card error: %s", exc)
            return None

    def _parse_job_detail(self, url: str) -> dict:
        result = {"description": "", "requirements": "", "salary_display": ""}
        response = self._make_request(url)
        if response is None:
            return result

        try:
            soup = BeautifulSoup(response.text, "html.parser")

            desc_el = soup.select_one(
                ".job-description, #job-description, .description, .job-detail"
            )
            if desc_el:
                result["description"] = desc_el.get_text(separator="\n", strip=True)

            req_el = soup.select_one(".requirements, .job-requirements")
            if req_el:
                result["requirements"] = req_el.get_text(separator="\n", strip=True)

            salary_el = soup.select_one(".salary, .compensation, .pay")
            if salary_el:
                result["salary_display"] = salary_el.get_text(strip=True)[:100]
        except Exception as exc:
            self.logger.debug("_parse_job_detail error for %s: %s", url, exc)

        return result
