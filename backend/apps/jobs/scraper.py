"""
Legacy scraper module — superseded by jobs/scrapers/ package.
Kept for backward compatibility.
"""
from .scrapers import RozeeScraper, IndeedScraper, LinkedInScraper

__all__ = ["RozeeScraper", "IndeedScraper", "LinkedInScraper"]
