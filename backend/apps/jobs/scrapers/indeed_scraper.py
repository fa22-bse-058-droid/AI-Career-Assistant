"""
Indeed (pk.indeed.com) job scraper.
"""
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


class IndeedScraper(BaseScraper):
    BASE_URL = "https://pk.indeed.com"

    def __init__(self):
        super().__init__(source="indeed")

    def fetch_jobs(self) -> int:
        total_found = 0

        for query in SEARCH_QUERIES:
            for page in range(3):  # 3 pages per query
                params = {
                    "q": query,
                    "l": "Pakistan",
                    "start": page * 10,
                }
                response = self._make_request(f"{self.BASE_URL}/jobs", params=params)
                if response is None:
                    # Check if it was a 403 — stop immediately and mark as partial
                    if self._last_status_code == 403:
                        self.logger.warning(
                            "Indeed returned 403 — stopping this source as partial"
                        )
                        if self.scraper_run:
                            type(self.scraper_run).objects.filter(
                                pk=self.scraper_run.pk
                            ).update(status="partial")
                        return total_found
                    self.log_error(
                        f"Failed to fetch indeed page {page} for query '{query}'"
                    )
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                cards = soup.select("[data-jk], .job_seen_beacon, .tapItem")
                if not cards:
                    break

                # Fetch detail for top 15 per query
                fetched_details = 0

                for card in cards:
                    # Skip sponsored results
                    if card.select_one(".sponsoredJob, [data-tn-component='sponsoredJob']"):
                        continue

                    job_data = self._parse_job_card(card)
                    if not job_data:
                        continue

                    job_url = job_data.get("url", "")
                    if self.job_exists(job_url):
                        self._increment_run_counter(jobs_skipped=1)
                        continue

                    if fetched_details < 15:
                        detail = self._parse_job_detail(job_url)
                        job_data.update(detail)
                        fetched_details += 1

                    experience_level = self._detect_experience_level(
                        job_data.get("title", ""),
                        job_data.get("description", ""),
                    )
                    job_data["experience_level"] = experience_level

                    _, created = self.save_job(job_data)
                    total_found += 1
                    if created:
                        self._increment_run_counter(jobs_found=1, jobs_added=1)
                    else:
                        self._increment_run_counter(jobs_found=1, jobs_updated=1)

        return total_found

    def _parse_job_card(self, card) -> dict | None:
        try:
            title_el = card.select_one("h2.jobTitle a, .jcs-JobTitle")
            company_el = card.select_one(
                ".companyName, [data-testid='company-name']"
            )
            location_el = card.select_one(
                ".companyLocation, [data-testid='text-location']"
            )
            link_el = card.select_one("a[href]")

            if not title_el or not link_el:
                return None

            href = link_el.get("href", "")
            if not href:
                return None
            if not href.startswith("http"):
                href = self.BASE_URL + href

            return {
                "title": title_el.get_text(strip=True),
                "company": company_el.get_text(strip=True) if company_el else "Unknown",
                "location": location_el.get_text(strip=True) if location_el else "",
                "url": href,
                "source": "indeed",
                "description": "",
                "requirements": "",
            }
        except Exception as exc:
            self.logger.debug("_parse_job_card error: %s", exc)
            return None

    def _parse_job_detail(self, url: str) -> dict:
        result = {"description": "", "requirements": ""}
        response = self._make_request(url)
        if response is None:
            return result

        try:
            soup = BeautifulSoup(response.text, "html.parser")
            desc_el = soup.select_one(
                "#jobDescriptionText, .jobsearch-jobDescriptionText"
            )
            if desc_el:
                result["description"] = desc_el.get_text(separator="\n", strip=True)
        except Exception as exc:
            self.logger.debug("_parse_job_detail error for %s: %s", url, exc)

        return result

    def _detect_experience_level(self, title: str, description: str) -> str:
        combined = f"{title} {description}".lower()
        if "intern" in combined or "internship" in combined:
            return "entry"
        if "senior" in combined or "lead" in combined:
            return "senior"
        if "1-2 years" in combined or "fresh" in combined:
            return "entry"
        return "any"
