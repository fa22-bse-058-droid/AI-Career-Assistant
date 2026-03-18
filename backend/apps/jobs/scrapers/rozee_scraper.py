"""
Rozee.pk job scraper.
"""
import logging

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

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
    source = "rozee"
    BASE_URL = "https://www.rozee.pk"
    SEARCH_QUERIES = SEARCH_QUERIES

    def fetch_jobs(self) -> int:
        """Scrape Rozee.pk for all search queries and save results."""
        total_added = 0

        for query in self.SEARCH_QUERIES:
            logger.info("[Rozee] Searching: %s", query)
            for page in range(1, 4):  # up to 3 pages
                url = f"{self.BASE_URL}/job/jsearch/q/{query.replace(' ', '+')}"
                params = {"fpn": page}
                resp = self._make_request(url, params=params)
                if resp is None:
                    logger.warning("[Rozee] No response for query=%s page=%d", query, page)
                    break

                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.select(".job-listing, .job-item, [data-job-id], .jlr")
                if not cards:
                    logger.info("[Rozee] No job cards on page %d for query=%s", page, query)
                    break

                for card in cards:
                    card_data = self._parse_job_card(card)
                    if not card_data:
                        continue

                    job_url = card_data.get("url", "")
                    if not job_url:
                        continue

                    if self.job_exists(job_url):
                        if self.scraper_run:
                            self.scraper_run.jobs_skipped += 1
                            self.scraper_run.jobs_found += 1
                            self.scraper_run.save(
                                update_fields=["jobs_skipped", "jobs_found"]
                            )
                        continue

                    # Fetch detail page for description
                    detail_data = self._parse_job_detail(job_url)
                    card_data.update(detail_data)

                    _, created = self.save_job(card_data)

                    if self.scraper_run:
                        self.scraper_run.jobs_found += 1
                        if created:
                            self.scraper_run.jobs_added += 1
                            total_added += 1
                        else:
                            self.scraper_run.jobs_updated += 1
                        self.scraper_run.save(
                            update_fields=["jobs_found", "jobs_added", "jobs_updated"]
                        )

        return total_added

    def _parse_job_card(self, card) -> dict | None:
        """Extract available fields from a Rozee job card element."""
        try:
            title_el = card.select_one(".job-title, h2 a, .title a, .jobtitle")
            company_el = card.select_one(".company-name, .company a, .comp-name")
            location_el = card.select_one(".location, .loc, .job-location")
            url_el = card.select_one("a[href]")

            if not title_el or not url_el:
                return None

            href = url_el.get("href", "")
            if not href:
                return None
            if not href.startswith("http"):
                href = self.BASE_URL + href

            title = title_el.get_text(strip=True)
            job_type = "internship" if "intern" in title.lower() else "full_time"

            return {
                "title": title,
                "company": company_el.get_text(strip=True) if company_el else "Unknown",
                "location": location_el.get_text(strip=True) if location_el else "",
                "url": href,
                "source": self.source,
                "job_type": job_type,
            }
        except Exception as exc:
            logger.debug("[Rozee] Error parsing job card: %s", exc)
            return None

    def _parse_job_detail(self, url: str) -> dict:
        """Fetch and parse the full job detail page."""
        result = {"description": "", "requirements": "", "salary_display": "", "raw_html": ""}
        try:
            resp = self._make_request(url)
            if resp is None:
                return result

            result["raw_html"] = resp.text[:50000]  # cap raw_html size
            soup = BeautifulSoup(resp.text, "html.parser")

            desc_el = soup.select_one(
                ".job-description, .description, #job-description, .job-detail"
            )
            if desc_el:
                result["description"] = desc_el.get_text(separator="\n", strip=True)

            req_el = soup.select_one(".job-requirements, .requirements, #requirements")
            if req_el:
                result["requirements"] = req_el.get_text(separator="\n", strip=True)

            salary_el = soup.select_one(".salary, .job-salary, .sal")
            if salary_el:
                result["salary_display"] = salary_el.get_text(strip=True)[:100]

        except Exception as exc:
            logger.warning("[Rozee] Error parsing job detail %s: %s", url, exc)

        return result
