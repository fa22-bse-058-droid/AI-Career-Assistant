"""
Job scraper implementations for Rozee.pk, Indeed, and LinkedIn.
"""
import logging
import random
import time
from datetime import timedelta
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)


def random_sleep(min_s=1.0, max_s=3.0):
    time.sleep(random.uniform(min_s, max_s))


def get_ua_headers():
    ua = UserAgent()
    return {"User-Agent": ua.random, "Accept-Language": "en-US,en;q=0.9"}


class RozeeScraper:
    BASE_URL = "https://www.rozee.pk/job/jsearch/q/all"

    def scrape(self, pages=3) -> list[dict]:
        jobs = []
        headers = get_ua_headers()
        for page in range(1, pages + 1):
            url = f"{self.BASE_URL}?fpn={page}"
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                for card in soup.select(".job-listing, .job-item, [data-job-id]"):
                    job = self._parse_card(card)
                    if job:
                        jobs.append(job)
                random_sleep()
            except Exception as e:
                logger.warning("Rozee scrape page %d failed: %s", page, e)
        return jobs

    def _parse_card(self, card) -> dict | None:
        try:
            title_el = card.select_one(".job-title, h2 a, .title a")
            company_el = card.select_one(".company-name, .company a")
            location_el = card.select_one(".location, .loc")
            url_el = card.select_one("a[href]")
            if not title_el or not url_el:
                return None
            url = url_el["href"]
            if not url.startswith("http"):
                url = "https://www.rozee.pk" + url
            return {
                "title": title_el.get_text(strip=True),
                "company": company_el.get_text(strip=True) if company_el else "Unknown",
                "location": location_el.get_text(strip=True) if location_el else "",
                "url": url,
                "source": "rozee",
                "description": "",
                "requirements": "",
            }
        except Exception:
            return None


class IndeedScraper:
    BASE_URL = "https://pk.indeed.com/jobs"

    def scrape(self, query="software developer", location="Pakistan", pages=3) -> list[dict]:
        jobs = []
        headers = get_ua_headers()
        for page in range(pages):
            params = {"q": query, "l": location, "start": page * 10}
            url = f"{self.BASE_URL}?{urlencode(params)}"
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                for card in soup.select("[data-jk], .job_seen_beacon, .tapItem"):
                    job = self._parse_card(card)
                    if job:
                        jobs.append(job)
                random_sleep()
            except Exception as e:
                logger.warning("Indeed scrape page %d failed: %s", page, e)
        return jobs

    def _parse_card(self, card) -> dict | None:
        try:
            title_el = card.select_one("h2.jobTitle a, .jcs-JobTitle")
            company_el = card.select_one(".companyName, [data-testid='company-name']")
            location_el = card.select_one(".companyLocation, [data-testid='text-location']")
            link_el = card.select_one("a[href]")
            if not title_el or not link_el:
                return None
            href = link_el["href"]
            if not href.startswith("http"):
                href = "https://pk.indeed.com" + href
            return {
                "title": title_el.get_text(strip=True),
                "company": company_el.get_text(strip=True) if company_el else "Unknown",
                "location": location_el.get_text(strip=True) if location_el else "",
                "url": href,
                "source": "indeed",
                "description": "",
                "requirements": "",
            }
        except Exception:
            return None


class LinkedInScraper:
    BASE_URL = "https://www.linkedin.com/jobs/search/"

    def scrape(self, keywords="software developer", location="Pakistan", pages=2) -> list[dict]:
        """LinkedIn scraper using Selenium headless Chrome."""
        jobs = []
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager

            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument(f"user-agent={UserAgent().random}")

            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options,
            )
            try:
                for page in range(pages):
                    params = urlencode({
                        "keywords": keywords,
                        "location": location,
                        "start": page * 25,
                    })
                    driver.get(f"{self.BASE_URL}?{params}")
                    wait = WebDriverWait(driver, 10)
                    try:
                        wait.until(EC.presence_of_element_located(
                            (By.CSS_SELECTOR, ".job-search-card, .base-card")
                        ))
                    except Exception:
                        pass
                    cards = driver.find_elements(By.CSS_SELECTOR, ".job-search-card, .base-card")
                    for card in cards:
                        job = self._parse_card_selenium(card)
                        if job:
                            jobs.append(job)
                    random_sleep(2, 4)
            finally:
                driver.quit()
        except Exception as e:
            logger.error("LinkedIn scraper failed: %s", e)
        return jobs

    def _parse_card_selenium(self, card) -> dict | None:
        try:
            from selenium.webdriver.common.by import By
            title_el = card.find_element(By.CSS_SELECTOR, "h3, .base-search-card__title")
            company_el = card.find_element(By.CSS_SELECTOR, "h4, .base-search-card__subtitle")
            location_el = card.find_element(By.CSS_SELECTOR, ".job-search-card__location, .base-search-card__metadata")
            link_el = card.find_element(By.CSS_SELECTOR, "a[href]")
            href = link_el.get_attribute("href") or ""
            if not href:
                return None
            return {
                "title": title_el.text.strip(),
                "company": company_el.text.strip() if company_el else "Unknown",
                "location": location_el.text.strip() if location_el else "",
                "url": href,
                "source": "linkedin",
                "description": "",
                "requirements": "",
            }
        except Exception:
            return None


def save_jobs(jobs: list[dict]) -> tuple[int, int]:
    """Save scraped jobs to database, skipping duplicates."""
    from .models import JobListing
    added = 0
    for job_data in jobs:
        url = job_data.get("url", "").strip()
        if not url:
            continue
        _, created = JobListing.objects.get_or_create(
            url=url,
            defaults={
                "title": job_data.get("title", "Unknown")[:255],
                "company": job_data.get("company", "Unknown")[:255],
                "location": job_data.get("location", "")[:255],
                "description": job_data.get("description", ""),
                "requirements": job_data.get("requirements", ""),
                "source": job_data.get("source", JobListing.Source.MANUAL),
            },
        )
        if created:
            added += 1
    return len(jobs), added
