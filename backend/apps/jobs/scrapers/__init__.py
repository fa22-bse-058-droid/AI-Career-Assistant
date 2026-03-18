"""
Job scrapers package.
"""
from .rozee_scraper import RozeeScraper
from .indeed_scraper import IndeedScraper
from .linkedin_scraper import LinkedInScraper
from .remotive_scraper import RemotiveScraper
from .weworkremotely_scraper import WeWorkRemotelyScraper
from .arbeitnow_scraper import ArbeitnowScraper
from .remoteok_scraper import RemoteOkScraper

__all__ = [
    "RozeeScraper",
    "IndeedScraper",
    "LinkedInScraper",
    "RemotiveScraper",
    "WeWorkRemotelyScraper",
    "ArbeitnowScraper",
    "RemoteOkScraper",
]
