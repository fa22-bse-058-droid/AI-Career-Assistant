"""
Indeed (pk.indeed.com) job scraper.
"""
import logging

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, SEARCH_QUERIES

logger = logging.getLogger(__name__)

_DETAIL_FETCH_LIMIT = 15  # avoid bans from over-fetching detail pages


class IndeedScraper(BaseScraper):
    source = "indeed"
    BASE_URL = "https://pk.indeed.com"
    SEARCH_QUERIES = SEARCH_QUERIES

    def fetch_jobs(self) -> int:
        """Scrape Indeed PK for all search queries and save results."""
        total_added = 0

        for query in self.SEARCH_QUERIES:
            logger.info("[Indeed] Searching: %s", query)
            detail_fetches_this_query = 0

            for page in range(3):  # 0, 1, 2 → 3 pages
                params = {"q": query, "l": "Pakistan", "start": page * 10}
                resp = self._make_request(self.BASE_URL + "/jobs", params=params)

                if resp is None:
                    logger.warning(
                        "[Indeed] No response for query=%s page=%d — stopping", query, page
                    )
                    # Mark as partial if we were blocked
                    if self.scraper_run:
                        from apps.jobs.models import ScraperRun
                        self.scraper_run.status = ScraperRun.Status.PARTIAL
                        self.scraper_run.save(update_fields=["status"])
                    break

                if resp.status_code == 403:
                    logger.warning("[Indeed] 403 received — stopping scraper")
                    if self.scraper_run:
                        from apps.jobs.models import ScraperRun
                        self.scraper_run.status = ScraperRun.Status.PARTIAL
                        self.scraper_run.save(update_fields=["status"])
                    return total_added

                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.select("[data-jk], .job_seen_beacon, .tapItem, .slider_item")
                if not cards:
                    logger.info("[Indeed] No cards on page %d for query=%s", page, query)
                    break

                # Filter sponsored
                cards = [c for c in cards if not c.select_one(".sponsoredJob, [data-hide-spinner]")]

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

                    # Only fetch detail pages for top N per query
                    if detail_fetches_this_query < _DETAIL_FETCH_LIMIT:
                        detail_data = self._parse_job_detail(job_url)
                        card_data.update(detail_data)
                        detail_fetches_this_query += 1

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
        """Extract available fields from an Indeed job card element."""
        try:
            title_el = card.select_one(
                "h2.jobTitle a, .jcs-JobTitle, [data-testid='jobTitle']"
            )
            company_el = card.select_one(
                ".companyName, [data-testid='company-name'], .css-1h7lukg"
            )
            location_el = card.select_one(
                ".companyLocation, [data-testid='text-location']"
            )
            link_el = card.select_one("a[href*='/rc/clk'], a[data-jk], h2.jobTitle a")

            if not title_el:
                return None

            href = ""
            if link_el:
                href = link_el.get("href", "")
                if href and not href.startswith("http"):
                    href = self.BASE_URL + href

            if not href:
                return None

            title = title_el.get_text(strip=True)
            experience_level = self._detect_experience_level(title, "")

            return {
                "title": title,
                "company": company_el.get_text(strip=True) if company_el else "Unknown",
                "location": location_el.get_text(strip=True) if location_el else "",
                "url": href,
                "source": self.source,
                "experience_level": experience_level,
                "job_type": "internship" if "intern" in title.lower() else "full_time",
            }
        except Exception as exc:
            logger.debug("[Indeed] Error parsing job card: %s", exc)
            return None

    def _parse_job_detail(self, url: str) -> dict:
        """Fetch and parse an Indeed job detail page."""
        result = {"description": "", "requirements": "", "raw_html": ""}
        try:
            resp = self._make_request(url)
            if resp is None:
                return result

            result["raw_html"] = resp.text[:50000]
            soup = BeautifulSoup(resp.text, "html.parser")

            desc_el = soup.select_one(
                "#jobDescriptionText, .jobsearch-jobDescriptionText, [data-testid='jobsearch-jobDescriptionText']"
            )
            if desc_el:
                full_text = desc_el.get_text(separator="\n", strip=True)
                result["description"] = full_text

                # Re-detect experience level now that we have full description
                # (will be merged by caller if needed)

        except Exception as exc:
            logger.warning("[Indeed] Error parsing job detail %s: %s", url, exc)

        return result

    def _detect_experience_level(self, title: str, description: str) -> str:
        """Heuristically determine experience level from title/description."""
        text = (title + " " + description).lower()
        if any(k in text for k in ("intern", "internship", "1-2 years", "fresh", "fresher", "graduate")):
            return "entry"
        if any(k in text for k in ("senior", "sr.", "lead", "principal", "head of")):
            return "senior"
        if "mid" in text or "2-4 years" in text or "3 years" in text:
            return "mid"
        return "any"
